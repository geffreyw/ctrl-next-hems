from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
import math


SUPER_DAL_START = time(1, 0)
SUPER_DAL_END = time(7, 0)
MORNING_PEAK_START = time(7, 0)
MORNING_PEAK_END = time(11, 0)
EVENING_PEAK_START = time(17, 0)
EVENING_PEAK_END = time(23, 0)

CONTROL_MODE_ANTI_FEED = "anti_feed"
CONTROL_MODE_PEAK_SHAVING = "peak_shaving"
SCENARIO_PEAK_ZERO_IMPORT = "peak_zero_import"
SCENARIO_SUPERDAL_CHARGE = "superdal_charge"
SCENARIO_LIMIT_IMPORT = "limit_import"
SCENARIO_USE_SURPLUS = "use_surplus"
SCENARIO_HOLD_RESERVE = "hold_reserve"
SCENARIO_SOLAR_SURPLUS = "solar_surplus"


@dataclass
class PlannerInputs:
    now: datetime
    current_soc_pct: float
    battery_nominal_kwh_each: float
    battery_count: int
    min_reserve_soc_pct: float
    safety_margin_pct: float
    import_limit_w: float
    max_grid_charge_power_w: float
    forecast_remaining_today_kwh: float
    forecast_tomorrow_kwh: float
    forecast_peak_today: datetime | None
    forecast_peak_tomorrow: datetime | None
    load_profile_w: list[float]


def _time_in_range(value: time, start: time, end: time) -> bool:
    return start <= value < end


def period_for_timestamp(ts: datetime) -> str:
    local_time = ts.time()
    if _time_in_range(local_time, SUPER_DAL_START, SUPER_DAL_END):
        return "super_dal"
    if _time_in_range(local_time, MORNING_PEAK_START, MORNING_PEAK_END):
        return "morning_peak"
    if _time_in_range(local_time, EVENING_PEAK_START, EVENING_PEAK_END):
        return "evening_peak"
    if local_time >= EVENING_PEAK_END or local_time < SUPER_DAL_START:
        return "night"
    return "day"


def _quarter_index(ts: datetime) -> int:
    return ts.hour * 4 + ts.minute // 15


def _next_quarter(ts: datetime) -> datetime:
    base = ts.replace(second=0, microsecond=0)
    minute = (base.minute // 15) * 15
    base = base.replace(minute=minute)
    if base < ts.replace(second=0, microsecond=0):
        base += timedelta(minutes=15)
    return base


def _build_timestamps(now: datetime) -> list[datetime]:
    start = _next_quarter(now)
    tomorrow = (now + timedelta(days=1)).date()
    end = datetime.combine(tomorrow, EVENING_PEAK_END, tzinfo=now.tzinfo)
    timestamps = []
    ts = start
    while ts <= end:
        timestamps.append(ts)
        ts += timedelta(minutes=15)
    return timestamps


def _solar_shape_weight(ts: datetime, peak: datetime | None) -> float:
    if ts.hour < 6 or ts.hour >= 21:
        return 0.0

    peak_hour = 13.0
    if peak is not None:
        peak_hour = peak.hour + peak.minute / 60.0

    hour = ts.hour + ts.minute / 60.0
    daylight_phase = math.sin(math.pi * max(0.0, min(1.0, (hour - 6.0) / 15.0)))
    peak_bias = math.exp(-((hour - peak_hour) ** 2) / 18.0)
    return max(0.0, daylight_phase * (0.6 + 0.4 * peak_bias))


def _build_solar_profile(
    timestamps: list[datetime],
    now: datetime,
    remaining_today_kwh: float,
    tomorrow_kwh: float,
    peak_today: datetime | None,
    peak_tomorrow: datetime | None,
) -> list[float]:
    solar_w = [0.0 for _ in timestamps]

    for target_date, energy_kwh, peak in [
        (now.date(), remaining_today_kwh, peak_today),
        ((now + timedelta(days=1)).date(), tomorrow_kwh, peak_tomorrow),
    ]:
        indices = [idx for idx, ts in enumerate(timestamps) if ts.date() == target_date]
        weights = [_solar_shape_weight(timestamps[idx], peak) for idx in indices]
        total_weight = sum(weights)
        if total_weight <= 0 or energy_kwh <= 0:
            continue
        # kWh in a 15 minute slot: W * 0.25h / 1000. Normalize weights to energy.
        for idx, weight in zip(indices, weights):
            slot_kwh = energy_kwh * weight / total_weight
            solar_w[idx] = slot_kwh * 1000.0 / 0.25

    return solar_w


def _sum_need_kwh(timestamps: list[datetime], load_w: list[float], solar_w: list[float], period: str) -> float:
    total = 0.0
    for idx, ts in enumerate(timestamps):
        if period_for_timestamp(ts) == period:
            total += max(load_w[idx] - solar_w[idx], 0.0) * 0.25 / 1000.0
    return total


def _day_charge_potential_kwh(timestamps: list[datetime], load_w: list[float], solar_w: list[float]) -> float:
    total = 0.0
    for idx, ts in enumerate(timestamps):
        if period_for_timestamp(ts) == "day":
            total += max(solar_w[idx] - load_w[idx], 0.0) * 0.25 / 1000.0
    return total


def build_plan(inputs: PlannerInputs) -> dict:
    timestamps = _build_timestamps(inputs.now)
    load_profile = inputs.load_profile_w or [800.0] * 96
    load_w = [max(load_profile[_quarter_index(ts) % len(load_profile)], 0.0) for ts in timestamps]
    solar_w = _build_solar_profile(
        timestamps,
        inputs.now,
        max(inputs.forecast_remaining_today_kwh, 0.0),
        max(inputs.forecast_tomorrow_kwh, 0.0),
        inputs.forecast_peak_today,
        inputs.forecast_peak_tomorrow,
    )

    total_capacity_kwh = max(inputs.battery_nominal_kwh_each * inputs.battery_count, 0.1)
    reserve_kwh = total_capacity_kwh * max(inputs.min_reserve_soc_pct, 0.0) / 100.0
    current_energy_kwh = total_capacity_kwh * max(0.0, min(100.0, inputs.current_soc_pct)) / 100.0
    margin = 1.0 + max(inputs.safety_margin_pct, 0.0) / 100.0

    morning_need_kwh = _sum_need_kwh(timestamps, load_w, solar_w, "morning_peak") * margin
    evening_need_kwh = _sum_need_kwh(timestamps, load_w, solar_w, "evening_peak") * margin
    day_charge_potential_kwh = _day_charge_potential_kwh(timestamps, load_w, solar_w)

    target_morning_kwh = min(total_capacity_kwh, reserve_kwh + morning_need_kwh)
    target_evening_kwh = min(total_capacity_kwh, reserve_kwh + evening_need_kwh)
    evening_deficit_kwh = max(evening_need_kwh - day_charge_potential_kwh, 0.0)
    target_after_super_dal_kwh = min(total_capacity_kwh, reserve_kwh + morning_need_kwh + evening_deficit_kwh)
    grid_charge_needed_kwh = max(target_after_super_dal_kwh - current_energy_kwh, 0.0)
    target_after_super_dal_soc = target_after_super_dal_kwh / total_capacity_kwh * 100.0

    energy_kwh = current_energy_kwh
    expected_soc = []
    expected_import_w = []
    mode = []
    reason = []
    control_mode = []
    peak_shaving_limit_w = []
    grid_charge_enabled = []
    grid_charge_target_soc = []
    grid_charge_max_power_w = []
    min_discharge_soc = []
    scenario = []
    super_dal_remaining_kwh = grid_charge_needed_kwh

    for idx, ts in enumerate(timestamps):
        period = period_for_timestamp(ts)
        load = load_w[idx]
        solar = solar_w[idx]
        net_load = load - solar
        slot_reason = "balans"
        slot_control_mode = CONTROL_MODE_PEAK_SHAVING
        slot_peak_limit_w = inputs.import_limit_w
        slot_grid_charge = False
        slot_grid_target_soc = 0.0
        slot_grid_max_power_w = 0.0
        slot_scenario = SCENARIO_HOLD_RESERVE

        if period in ("morning_peak", "evening_peak"):
            protected_kwh = reserve_kwh
            target_import_w = 0.0
            slot_control_mode = CONTROL_MODE_ANTI_FEED
            slot_peak_limit_w = 0.0
            slot_scenario = SCENARIO_PEAK_ZERO_IMPORT
            slot_reason = "piek naar 0W import"
        elif period == "super_dal" and super_dal_remaining_kwh > 0:
            protected_kwh = target_after_super_dal_kwh
            target_import_w = inputs.import_limit_w
            headroom_w = max(inputs.import_limit_w - load, 0.0)
            slot_grid_max_power_w = min(
                inputs.max_grid_charge_power_w,
                headroom_w,
                super_dal_remaining_kwh * 1000.0 / 0.25,
            )
            slot_grid_charge = slot_grid_max_power_w > 0.0
            slot_grid_target_soc = target_after_super_dal_soc
            slot_scenario = SCENARIO_SUPERDAL_CHARGE if slot_grid_charge else SCENARIO_HOLD_RESERVE
            slot_reason = "superdal laden binnen importlimiet"
            if not slot_grid_charge and net_load > inputs.import_limit_w:
                protected_kwh = reserve_kwh
                slot_scenario = SCENARIO_LIMIT_IMPORT
                slot_reason = "import begrenzen tijdens superdal"
        else:
            if ts.time() < SUPER_DAL_END:
                protected_kwh = target_after_super_dal_kwh
            elif ts.time() < MORNING_PEAK_START:
                protected_kwh = target_morning_kwh
            elif ts.time() < EVENING_PEAK_START:
                protected_kwh = target_evening_kwh
            elif ts.time() >= EVENING_PEAK_END:
                protected_kwh = target_morning_kwh
            else:
                protected_kwh = reserve_kwh

            surplus_kwh = max(energy_kwh - protected_kwh, 0.0)
            if surplus_kwh > 0:
                target_import_w = 0.0
                slot_control_mode = CONTROL_MODE_ANTI_FEED
                slot_peak_limit_w = 0.0
                slot_scenario = SCENARIO_USE_SURPLUS
                slot_reason = "overschot gebruiken"
            else:
                target_import_w = inputs.import_limit_w
                slot_scenario = SCENARIO_LIMIT_IMPORT if net_load > inputs.import_limit_w else SCENARIO_HOLD_RESERVE
                slot_reason = "import begrenzen" if net_load > inputs.import_limit_w else "reserve bewaren"

        if net_load < 0:
            slot_scenario = SCENARIO_SOLAR_SURPLUS
            slot_reason = "solaroverschot laadt batterij"

        if net_load < 0:
            charge_kwh = min(-net_load * 0.25 / 1000.0, total_capacity_kwh - energy_kwh)
            energy_kwh += max(charge_kwh, 0.0)
            grid_import = 0.0
        elif slot_grid_charge:
            charge_w = slot_grid_max_power_w
            charge_kwh = max(charge_w, 0.0) * 0.25 / 1000.0
            energy_kwh = min(total_capacity_kwh, energy_kwh + charge_kwh)
            super_dal_remaining_kwh = max(super_dal_remaining_kwh - charge_kwh, 0.0)
            grid_import = min(load + charge_w, inputs.import_limit_w)
        else:
            desired_discharge_w = max(net_load - target_import_w, 0.0)
            available_discharge_kwh = max(energy_kwh - protected_kwh, 0.0)
            discharge_kwh = min(desired_discharge_w * 0.25 / 1000.0, available_discharge_kwh)
            energy_kwh = max(reserve_kwh, energy_kwh - discharge_kwh)
            grid_import = max(net_load - discharge_kwh * 1000.0 / 0.25, 0.0)

        energy_kwh = max(0.0, min(total_capacity_kwh, energy_kwh))
        expected_soc.append(round(energy_kwh / total_capacity_kwh * 100.0, 1))
        expected_import_w.append(round(grid_import, 0))
        mode.append(period)
        reason.append(slot_reason)
        control_mode.append(slot_control_mode)
        peak_shaving_limit_w.append(round(slot_peak_limit_w, 0))
        grid_charge_enabled.append(slot_grid_charge)
        grid_charge_target_soc.append(round(slot_grid_target_soc, 0))
        grid_charge_max_power_w.append(round(slot_grid_max_power_w, 0))
        min_discharge_soc.append(round(protected_kwh / total_capacity_kwh * 100.0, 1))
        scenario.append(slot_scenario)

    expected_min_soc = min(expected_soc) if expected_soc else inputs.current_soc_pct
    free_surplus_kwh = max(current_energy_kwh - target_after_super_dal_kwh, 0.0)
    current_headroom_w = max(inputs.import_limit_w - (load_w[0] if load_w else 0.0), 0.0)
    planned_grid_charge_power_w = min(inputs.max_grid_charge_power_w, current_headroom_w) if grid_charge_needed_kwh > 0 else 0.0
    planned_grid_charge_kwh = sum(value * 0.25 / 1000.0 for value in grid_charge_max_power_w)

    if grid_charge_needed_kwh > 0 and planned_grid_charge_kwh > 0:
        if planned_grid_charge_kwh + 0.01 < grid_charge_needed_kwh:
            summary = (
                f"Smart kan {planned_grid_charge_kwh:.2f} van {grid_charge_needed_kwh:.2f} kWh "
                "superdal-laden plannen binnen max netlaadvermogen en importlimiet."
            )
        else:
            summary = (
                f"Smart plant {grid_charge_needed_kwh:.2f} kWh superdal-laden tot "
                f"{target_after_super_dal_kwh / total_capacity_kwh * 100:.0f}% om piekuren te dekken."
            )
    elif grid_charge_needed_kwh > 0:
        summary = (
            f"Smart heeft {grid_charge_needed_kwh:.2f} kWh superdal-laden nodig, "
            "maar er is geen laadvermogen gepland. Controleer max netlaadvermogen en importlimiet."
        )
    else:
        summary = (
            f"Geen superdal-laden nodig. Verwachte minimum SoC {expected_min_soc:.0f}% "
            f"blijft boven reserve."
        )

    return {
        "summary": summary,
        "target_soc_morning": round(target_morning_kwh / total_capacity_kwh * 100.0, 0),
        "target_soc_evening": round(target_evening_kwh / total_capacity_kwh * 100.0, 0),
        "target_soc_after_super_dal": round(target_after_super_dal_kwh / total_capacity_kwh * 100.0, 0),
        "grid_charge_needed_kwh": round(grid_charge_needed_kwh, 2),
        "planned_grid_charge_power_w": round(planned_grid_charge_power_w, 0),
        "planned_grid_charge_kwh": round(planned_grid_charge_kwh, 2),
        "current_headroom_w": round(current_headroom_w, 0),
        "expected_min_soc": round(expected_min_soc, 1),
        "free_surplus_kwh": round(free_surplus_kwh, 2),
        "morning_need_kwh": round(morning_need_kwh, 2),
        "evening_need_kwh": round(evening_need_kwh, 2),
        "day_charge_potential_kwh": round(day_charge_potential_kwh, 2),
        "timestamps": [ts.isoformat() for ts in timestamps],
        "expected_soc": expected_soc,
        "expected_load_w": [round(value, 0) for value in load_w],
        "expected_solar_w": [round(value, 0) for value in solar_w],
        "expected_import_w": expected_import_w,
        "mode": mode,
        "reasons": reason,
        "control_mode": control_mode,
        "peak_shaving_limit_w": peak_shaving_limit_w,
        "grid_charge_enabled": grid_charge_enabled,
        "grid_charge_target_soc": grid_charge_target_soc,
        "grid_charge_max_power_w": grid_charge_max_power_w,
        "min_discharge_soc": min_discharge_soc,
        "scenario": scenario,
        "profile_quality": "history_or_fallback",
    }

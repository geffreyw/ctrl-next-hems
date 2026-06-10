from datetime import datetime, timedelta
from pathlib import Path
import sys
import types

_REPO_DIR = Path(__file__).resolve().parents[1]
_PACKAGE_PARENT = _REPO_DIR.parent
sys.path = [
    path
    for path in sys.path
    if Path(path or ".").resolve() != _REPO_DIR
]
sys.path.insert(0, str(_PACKAGE_PARENT))


def _install_homeassistant_stubs():
    aiohttp = types.ModuleType("aiohttp")
    homeassistant = types.ModuleType("homeassistant")
    config_entries = types.ModuleType("homeassistant.config_entries")
    const = types.ModuleType("homeassistant.const")
    core = types.ModuleType("homeassistant.core")
    helpers = types.ModuleType("homeassistant.helpers")
    dispatcher = types.ModuleType("homeassistant.helpers.dispatcher")
    aiohttp_client = types.ModuleType("homeassistant.helpers.aiohttp_client")

    class ConfigEntry:
        pass

    class HomeAssistant:
        pass

    class ClientError(Exception):
        pass

    aiohttp.ClientError = ClientError
    config_entries.ConfigEntry = ConfigEntry
    const.EVENT_HOMEASSISTANT_STOP = "homeassistant_stop"
    core.HomeAssistant = HomeAssistant
    dispatcher.async_dispatcher_send = lambda *args, **kwargs: None
    aiohttp_client.async_get_clientsession = lambda hass: None

    sys.modules.setdefault("aiohttp", aiohttp)
    sys.modules.setdefault("homeassistant", homeassistant)
    sys.modules.setdefault("homeassistant.config_entries", config_entries)
    sys.modules.setdefault("homeassistant.const", const)
    sys.modules.setdefault("homeassistant.core", core)
    sys.modules.setdefault("homeassistant.helpers", helpers)
    sys.modules.setdefault("homeassistant.helpers.dispatcher", dispatcher)
    sys.modules.setdefault("homeassistant.helpers.aiohttp_client", aiohttp_client)


_install_homeassistant_stubs()

from ctrl_next_hems.const import (  # noqa: E402
    CONF_FORECAST_SOLAR_PEAK_TODAY,
    CONF_FORECAST_SOLAR_PEAK_TOMORROW,
    CONF_FORECAST_SOLAR_REMAINING_TODAY,
    CONF_FORECAST_SOLAR_TOMORROW,
)
from ctrl_next_hems.controller import CtrlNextController  # noqa: E402
from ctrl_next_hems.planner import PlannerInputs, build_plan  # noqa: E402


class _State:
    def __init__(self, state):
        self.state = state


class _States:
    def __init__(self, values):
        self._values = values

    def get(self, entity_id):
        value = self._values.get(entity_id)
        if value is None:
            return None
        return _State(value)


class _Hass:
    def __init__(self, values):
        self.states = _States(values)


def _controller(values):
    controller = CtrlNextController.__new__(CtrlNextController)
    controller.hass = _Hass(values)
    controller.config = {
        CONF_FORECAST_SOLAR_REMAINING_TODAY: "sensor.remaining",
        CONF_FORECAST_SOLAR_TOMORROW: "sensor.tomorrow",
        CONF_FORECAST_SOLAR_PEAK_TODAY: "sensor.peak_today",
        CONF_FORECAST_SOLAR_PEAK_TOMORROW: "sensor.peak_tomorrow",
    }
    controller._forecast_cache = {}
    return controller


def _live_values():
    return {
        "sensor.remaining": "8.03",
        "sensor.tomorrow": "11.32",
        "sensor.peak_today": "2026-06-10T12:00:00+00:00",
        "sensor.peak_tomorrow": "2026-06-11T11:00:00+00:00",
    }


def _unavailable_values():
    return {
        "sensor.remaining": "unavailable",
        "sensor.tomorrow": "unavailable",
        "sensor.peak_today": "unavailable",
        "sensor.peak_tomorrow": "unavailable",
    }


def test_live_forecast_updates_cache():
    now = datetime.fromisoformat("2026-06-10T12:30:00+02:00")
    controller = _controller(_live_values())

    result = controller._get_forecast_inputs(now)

    assert result["forecast_quality"] == "live"
    assert result["forecast_remaining_today_kwh"] == 8.03
    assert result["forecast_tomorrow_kwh"] == 11.32
    assert result["forecast_cached_since"] is None
    assert "forecast_remaining_today_kwh" in controller._forecast_cache


def test_unavailable_forecast_uses_fresh_cache():
    now = datetime.fromisoformat("2026-06-10T12:30:00+02:00")
    controller = _controller(_live_values())
    controller._get_forecast_inputs(now)
    controller.hass = _Hass(_unavailable_values())

    result = controller._get_forecast_inputs(now + timedelta(hours=1))

    assert result["forecast_quality"] == "cached"
    assert result["forecast_remaining_today_kwh"] == 8.03
    assert result["forecast_tomorrow_kwh"] == 11.32
    assert result["forecast_cached_since"] == now.isoformat()
    assert result["forecast_cache_age_minutes"] == 60


def test_unavailable_forecast_without_cache_falls_back_to_zero():
    now = datetime.fromisoformat("2026-06-10T12:30:00+02:00")
    controller = _controller(_unavailable_values())

    result = controller._get_forecast_inputs(now)

    assert result["forecast_quality"] == "fallback_zero"
    assert result["forecast_remaining_today_kwh"] == 0.0
    assert result["forecast_tomorrow_kwh"] == 0.0
    assert result["forecast_peak_today"] is None
    assert result["forecast_cached_since"] is None


def test_unavailable_forecast_ignores_stale_cache():
    now = datetime.fromisoformat("2026-06-10T12:30:00+02:00")
    controller = _controller(_live_values())
    controller._get_forecast_inputs(now)
    controller.hass = _Hass(_unavailable_values())

    result = controller._get_forecast_inputs(now + timedelta(hours=3, minutes=1))

    assert result["forecast_quality"] == "fallback_zero"
    assert result["forecast_remaining_today_kwh"] == 0.0
    assert result["forecast_cached_since"] is None


def test_cached_forecast_prevents_zero_solar_regression():
    now = datetime.fromisoformat("2026-06-10T12:49:15+02:00")
    controller = _controller(_live_values())
    controller._get_forecast_inputs(now - timedelta(minutes=20))
    controller.hass = _Hass(_unavailable_values())
    forecast = controller._get_forecast_inputs(now)

    plan = build_plan(
        PlannerInputs(
            now=now,
            current_soc_pct=98.3,
            battery_nominal_kwh_each=5.12,
            battery_count=2,
            min_reserve_soc_pct=15.0,
            safety_margin_pct=15.0,
            import_limit_w=2200.0,
            max_grid_charge_power_w=500.0,
            forecast_remaining_today_kwh=forecast["forecast_remaining_today_kwh"],
            forecast_tomorrow_kwh=forecast["forecast_tomorrow_kwh"],
            forecast_peak_today=forecast["forecast_peak_today"],
            forecast_peak_tomorrow=forecast["forecast_peak_tomorrow"],
            load_profile_w=[800.0] * 96,
        )
    )

    assert forecast["forecast_quality"] == "cached"
    assert plan["day_charge_potential_kwh"] > 0
    assert plan["free_surplus_kwh"] > 0
    assert plan["target_soc_evening"] < 100

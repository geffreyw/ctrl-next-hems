import asyncio
from datetime import datetime, timedelta
from functools import partial
import logging
import time
from urllib.parse import urlsplit

from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send # NIEUW
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import (
    CONF_BAT1_CHARGE,
    CONF_BAT1_AC_POWER,
    CONF_BAT1_DISCHARGE,
    CONF_BAT1_FORCE_MODE,
    CONF_BAT1_MODBUS_SWITCH,
    CONF_BAT1_WORK_MODE,
    CONF_BAT2_CHARGE,
    CONF_BAT2_AC_POWER,
    CONF_BAT2_DISCHARGE,
    CONF_BAT2_FORCE_MODE,
    CONF_BAT2_MODBUS_SWITCH,
    CONF_BAT2_WORK_MODE,
    CONF_BATTERY_1_SOC,
    CONF_BATTERY_2_SOC,
    CONF_CONTROL_MODE,
    CONF_FORECAST_SOLAR_NEXT_HOUR,
    CONF_FORECAST_SOLAR_PEAK_TODAY,
    CONF_FORECAST_SOLAR_PEAK_TOMORROW,
    CONF_FORECAST_SOLAR_POWER_IN_24H,
    CONF_FORECAST_SOLAR_POWER_NOW,
    CONF_FORECAST_SOLAR_REMAINING_TODAY,
    CONF_FORECAST_SOLAR_THIS_HOUR,
    CONF_FORECAST_SOLAR_TODAY,
    CONF_FORECAST_SOLAR_TOMORROW,
    CONF_OPERATING_MODE,
    CONF_PLANNER_BATTERY_COUNT,
    CONF_PLANNER_BATTERY_NOMINAL_KWH_EACH,
    CONF_PLANNER_DASHBOARD_PATH,
    CONF_PLANNER_IMPORT_LIMIT_W,
    CONF_PLANNER_MIN_RESERVE_SOC,
    CONF_PLANNER_NOTIFY_SERVICE,
    CONF_PLANNER_SAFETY_MARGIN_PCT,
    CONTROL_MODE_ANTI_FEED,
    CONTROL_MODE_PEAK_SHAVING,
    DEFAULT_BAT1_AC_POWER,
    DEFAULT_BAT1_CHARGE,
    DEFAULT_BAT1_DISCHARGE,
    DEFAULT_BAT1_FORCE_MODE,
    DEFAULT_BAT1_MODBUS_SWITCH,
    DEFAULT_BAT1_WORK_MODE,
    DEFAULT_BAT2_AC_POWER,
    DEFAULT_BAT2_CHARGE,
    DEFAULT_BAT2_DISCHARGE,
    DEFAULT_BAT2_FORCE_MODE,
    DEFAULT_BAT2_MODBUS_SWITCH,
    DEFAULT_BAT2_WORK_MODE,
    DEFAULT_BATTERY_1_SOC,
    DEFAULT_BATTERY_2_SOC,
    DEFAULT_FORECAST_SOLAR_NEXT_HOUR,
    DEFAULT_FORECAST_SOLAR_PEAK_TODAY,
    DEFAULT_FORECAST_SOLAR_PEAK_TOMORROW,
    DEFAULT_FORECAST_SOLAR_POWER_IN_24H,
    DEFAULT_FORECAST_SOLAR_POWER_NOW,
    DEFAULT_FORECAST_SOLAR_REMAINING_TODAY,
    DEFAULT_FORECAST_SOLAR_THIS_HOUR,
    DEFAULT_FORECAST_SOLAR_TODAY,
    DEFAULT_FORECAST_SOLAR_TOMORROW,
    DEFAULT_OPERATING_MODE,
    DEFAULT_P1_IP_ADDRESS,
    DEFAULT_P1_SENSOR,
    DEFAULT_PLANNER_BATTERY_COUNT,
    DEFAULT_PLANNER_BATTERY_NOMINAL_KWH_EACH,
    DEFAULT_PLANNER_DASHBOARD_PATH,
    DEFAULT_PLANNER_IMPORT_LIMIT_W,
    DEFAULT_PLANNER_MIN_RESERVE_SOC,
    DEFAULT_PLANNER_NOTIFY_SERVICE,
    DEFAULT_PLANNER_SAFETY_MARGIN_PCT,
    OPERATING_MODE_MANUAL,
    OPERATING_MODE_OFF,
    OPERATING_MODE_SMART,
    OPERATING_MODES,
    CONF_P1_IP_ADDRESS,
    CONF_P1_SENSOR,
)
from .planner import (
    EVENING_PEAK_END,
    EVENING_PEAK_START,
    MORNING_PEAK_START,
    SUPER_DAL_END,
    PlannerInputs,
    build_plan,
    period_for_timestamp,
)

_LOGGER = logging.getLogger(__name__)

# Marstek Venus E V3 — vaste waarden
_FORCE_MODE_STOP       = "stop"
_FORCE_MODE_CHARGE     = "charge"
_FORCE_MODE_DISCHARGE  = "discharge"
_WORK_MODE_ANTI_FEED   = "anti_feed"
_DEFAULT_PEAK_SHAVING_LIMIT_W = 2200.0
_DEFAULT_GRID_CHARGE_TARGET_SOC = 100.0
_DEFAULT_GRID_CHARGE_MAX_POWER_W = 500.0

# Hardware minimum SoC is ~12%; 14% geeft 2% softwaremarge zodat we geen
# ontlaadopdrachten sturen terwijl de batterij al bijna bij zijn hardwaregrens zit.
_SOC_MIN_DISCHARGE = 14.0
# Boven 99% heeft laden geen zin meer.
_SOC_MAX_CHARGE    = 99.0
_HOMEWIZARD_DATA_PATH = "/api/v1/data"
_P1_HTTP_TIMEOUT_SECONDS = 2.0
_SMART_PLAN_DISPATCH = "ctrl_next_plan_update"

DEFAULT_CONFIG = {
    CONF_P1_SENSOR: DEFAULT_P1_SENSOR,
    CONF_P1_IP_ADDRESS: DEFAULT_P1_IP_ADDRESS,
    CONF_BATTERY_1_SOC: DEFAULT_BATTERY_1_SOC,
    CONF_BAT1_AC_POWER: DEFAULT_BAT1_AC_POWER,
    CONF_BAT1_CHARGE: DEFAULT_BAT1_CHARGE,
    CONF_BAT1_DISCHARGE: DEFAULT_BAT1_DISCHARGE,
    CONF_BAT1_FORCE_MODE: DEFAULT_BAT1_FORCE_MODE,
    CONF_BAT1_MODBUS_SWITCH: DEFAULT_BAT1_MODBUS_SWITCH,
    CONF_BAT1_WORK_MODE: DEFAULT_BAT1_WORK_MODE,
    CONF_BATTERY_2_SOC: DEFAULT_BATTERY_2_SOC,
    CONF_BAT2_AC_POWER: DEFAULT_BAT2_AC_POWER,
    CONF_BAT2_CHARGE: DEFAULT_BAT2_CHARGE,
    CONF_BAT2_DISCHARGE: DEFAULT_BAT2_DISCHARGE,
    CONF_BAT2_FORCE_MODE: DEFAULT_BAT2_FORCE_MODE,
    CONF_BAT2_MODBUS_SWITCH: DEFAULT_BAT2_MODBUS_SWITCH,
    CONF_BAT2_WORK_MODE: DEFAULT_BAT2_WORK_MODE,
    CONF_FORECAST_SOLAR_TODAY: DEFAULT_FORECAST_SOLAR_TODAY,
    CONF_FORECAST_SOLAR_REMAINING_TODAY: DEFAULT_FORECAST_SOLAR_REMAINING_TODAY,
    CONF_FORECAST_SOLAR_TOMORROW: DEFAULT_FORECAST_SOLAR_TOMORROW,
    CONF_FORECAST_SOLAR_THIS_HOUR: DEFAULT_FORECAST_SOLAR_THIS_HOUR,
    CONF_FORECAST_SOLAR_NEXT_HOUR: DEFAULT_FORECAST_SOLAR_NEXT_HOUR,
    CONF_FORECAST_SOLAR_POWER_NOW: DEFAULT_FORECAST_SOLAR_POWER_NOW,
    CONF_FORECAST_SOLAR_POWER_IN_24H: DEFAULT_FORECAST_SOLAR_POWER_IN_24H,
    CONF_FORECAST_SOLAR_PEAK_TODAY: DEFAULT_FORECAST_SOLAR_PEAK_TODAY,
    CONF_FORECAST_SOLAR_PEAK_TOMORROW: DEFAULT_FORECAST_SOLAR_PEAK_TOMORROW,
    CONF_PLANNER_NOTIFY_SERVICE: DEFAULT_PLANNER_NOTIFY_SERVICE,
    CONF_PLANNER_DASHBOARD_PATH: DEFAULT_PLANNER_DASHBOARD_PATH,
    CONF_PLANNER_BATTERY_NOMINAL_KWH_EACH: DEFAULT_PLANNER_BATTERY_NOMINAL_KWH_EACH,
    CONF_PLANNER_BATTERY_COUNT: DEFAULT_PLANNER_BATTERY_COUNT,
    CONF_PLANNER_MIN_RESERVE_SOC: DEFAULT_PLANNER_MIN_RESERVE_SOC,
    CONF_PLANNER_SAFETY_MARGIN_PCT: DEFAULT_PLANNER_SAFETY_MARGIN_PCT,
    CONF_PLANNER_IMPORT_LIMIT_W: DEFAULT_PLANNER_IMPORT_LIMIT_W,
    CONF_OPERATING_MODE: OPERATING_MODE_MANUAL,
}

class CtrlNextController:
    def __init__(self, hass: HomeAssistant, config_data: dict):
        self.hass = hass
        self.config = {**DEFAULT_CONFIG, **config_data}
        self.running = False
        self.operating_mode = self.config.get(CONF_OPERATING_MODE, DEFAULT_OPERATING_MODE)
        if self.operating_mode not in OPERATING_MODES:
            self.operating_mode = OPERATING_MODE_MANUAL
        self.enabled = self.operating_mode != OPERATING_MODE_OFF
        self._task = None
        
        self.virtual_bat_power = {"1": 0.0, "2": 0.0}
        self.p1_used_value = 0.0
        self.huisverbruik_value = 0.0

        self._http_session = async_get_clientsession(hass)
        self._p1_ip_address = self._normalize_host(self.config.get(CONF_P1_IP_ADDRESS) or "")
        self._p1_http_url = self._build_p1_data_url(self._p1_ip_address)

        # Backward compatibility: bestaande installaties met oude URL-setting.
        if not self._p1_http_url:
            self._p1_http_url = self._normalize_legacy_url(self.config.get("p1_http_url") or "")

        self._last_http_error_log = 0.0

        self.control_modes = [CONTROL_MODE_ANTI_FEED, CONTROL_MODE_PEAK_SHAVING]
        self.control_mode = self.config.get(CONF_CONTROL_MODE, CONTROL_MODE_ANTI_FEED)
        if self.control_mode not in self.control_modes:
            _LOGGER.warning(
                "Onbekende control_mode '%s', fallback naar '%s'",
                self.control_mode,
                CONTROL_MODE_ANTI_FEED,
            )
            self.control_mode = CONTROL_MODE_ANTI_FEED
        self.manual_control_mode = self.control_mode

        self.max_power_per_bat = 2500.0

        # Regelparameters (configureerbaar via number-entities).
        self.peak_shaving_limit_w = _DEFAULT_PEAK_SHAVING_LIMIT_W
        self.grid_charge_enabled = False
        self.grid_charge_target_soc = _DEFAULT_GRID_CHARGE_TARGET_SOC
        self.grid_charge_max_power_w = _DEFAULT_GRID_CHARGE_MAX_POWER_W
        self.deadband = 15.0 
        self.cache_threshold = 25.0
        self.planner_battery_nominal_kwh_each = float(self.config.get(CONF_PLANNER_BATTERY_NOMINAL_KWH_EACH, DEFAULT_PLANNER_BATTERY_NOMINAL_KWH_EACH))
        self.planner_battery_count = float(self.config.get(CONF_PLANNER_BATTERY_COUNT, DEFAULT_PLANNER_BATTERY_COUNT))
        self.planner_min_reserve_soc = float(self.config.get(CONF_PLANNER_MIN_RESERVE_SOC, DEFAULT_PLANNER_MIN_RESERVE_SOC))
        self.planner_safety_margin_pct = float(self.config.get(CONF_PLANNER_SAFETY_MARGIN_PCT, DEFAULT_PLANNER_SAFETY_MARGIN_PCT))
        self.planner_import_limit_w = float(self.config.get(CONF_PLANNER_IMPORT_LIMIT_W, DEFAULT_PLANNER_IMPORT_LIMIT_W))

        # Anti-oscillatie parameters voor 1s loop.
        self.filter_alpha = 0.35
        self.deadband_release_margin = 35.0
        self.min_power_per_bat = 120.0
        self.max_power_step_per_cycle = 300.0
        self.min_mode_hold_seconds = 3.0

        self._filtered_huisverbruik = 0.0
        self._global_mode = _FORCE_MODE_STOP
        self._last_global_mode_change = 0.0
        self._service_lock = asyncio.Lock()
        
        self.last_mode = {"1": _FORCE_MODE_STOP, "2": _FORCE_MODE_STOP}
        self.last_power = {"1": 0.0, "2": 0.0}
        self.smart_plan = self._empty_plan()
        self.smart_active_profile = self._empty_smart_profile()
        self._manual_control_settings = {}
        self._capture_manual_control_settings()
        self._last_plan_refresh = None
        self._last_plan_notification_date = None

    async def start(self):
        self.running = True
        self._task = self.hass.async_create_background_task(self._loop(), "CTRL-NEXT HEMS Loop")

    async def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._set_all_batteries_failsafe("controller gestopt")

    def get_operating_mode(self) -> str:
        return self.operating_mode

    def invalidate_smart_plan(self):
        self._last_plan_refresh = None
        async_dispatcher_send(self.hass, _SMART_PLAN_DISPATCH)

    async def set_operating_mode(self, mode: str):
        if mode not in OPERATING_MODES:
            _LOGGER.warning("Ongeldige operating mode ontvangen: %s", mode)
            return

        if mode == self.operating_mode:
            return

        previous_mode = self.operating_mode
        if previous_mode == OPERATING_MODE_MANUAL:
            self.manual_control_mode = self.control_mode
            self._capture_manual_control_settings()

        _LOGGER.info("Bedrijfsmodus gewijzigd van '%s' naar '%s'", self.operating_mode, mode)
        self.operating_mode = mode
        self.enabled = mode != OPERATING_MODE_OFF

        if mode == OPERATING_MODE_OFF:
            await self._set_all_batteries_failsafe("bedrijfsmodus off")
        else:
            if mode == OPERATING_MODE_MANUAL:
                self._restore_manual_control_settings()
                self.set_control_mode(self.manual_control_mode, remember_manual=False)
            self.last_mode = {"1": "Unknown", "2": "Unknown"}
            self.last_power = {"1": -1.0, "2": -1.0}
            async_dispatcher_send(self.hass, "ctrl_next_update")
            async_dispatcher_send(self.hass, _SMART_PLAN_DISPATCH)

    async def set_enabled(self, status: bool):
        await self.set_operating_mode(OPERATING_MODE_MANUAL if status else OPERATING_MODE_OFF)

    def _get_float_state(self, entity_id):
        # Voorkom crash als de configuratie leeg is
        if not entity_id:
            return 0.0
            
        state = self.hass.states.get(entity_id)
        if state and state.state not in ["unknown", "unavailable"]:
            try: 
                return float(state.state)
            except ValueError: 
                return 0.0
        return 0.0

    def _get_battery_entities(self, bat_idx):
        mapping = {
            "1": {
                "charge": self.config.get(CONF_BAT1_CHARGE),
                "discharge": self.config.get(CONF_BAT1_DISCHARGE),
                "force_mode": self.config.get(CONF_BAT1_FORCE_MODE),
                "modbus_switch": self.config.get(CONF_BAT1_MODBUS_SWITCH),
                "work_mode": self.config.get(CONF_BAT1_WORK_MODE),
            },
            "2": {
                "charge": self.config.get(CONF_BAT2_CHARGE),
                "discharge": self.config.get(CONF_BAT2_DISCHARGE),
                "force_mode": self.config.get(CONF_BAT2_FORCE_MODE),
                "modbus_switch": self.config.get(CONF_BAT2_MODBUS_SWITCH),
                "work_mode": self.config.get(CONF_BAT2_WORK_MODE),
            },
        }
        return mapping[bat_idx]

    @staticmethod
    def _normalize_host(host_value):
        host = (host_value or "").strip()
        if not host:
            return ""

        # Laat zowel "192.168.1.10" als "http://192.168.1.10" toe.
        if "://" in host:
            parsed = urlsplit(host)
            host = parsed.netloc or parsed.path

        return host.split("/")[0].strip()

    def _build_p1_data_url(self, host_value):
        host = self._normalize_host(host_value)
        if not host:
            return ""
        return f"http://{host}{_HOMEWIZARD_DATA_PATH}"

    def _normalize_legacy_url(self, url_value):
        legacy_url = (url_value or "").strip().rstrip("/")
        if not legacy_url:
            return ""

        # Als oude config al direct naar /api/v1/data wijst, behouden.
        if legacy_url.endswith(_HOMEWIZARD_DATA_PATH):
            return legacy_url

        # Als enkel host geconfigureerd stond, converteer naar hardcoded endpoint.
        return self._build_p1_data_url(legacy_url)

    def _capture_manual_control_settings(self):
        self._manual_control_settings = {
            "peak_shaving_limit_w": self.peak_shaving_limit_w,
            "grid_charge_enabled": self.grid_charge_enabled,
            "grid_charge_target_soc": self.grid_charge_target_soc,
            "grid_charge_max_power_w": self.grid_charge_max_power_w,
        }

    def _restore_manual_control_settings(self):
        if not self._manual_control_settings:
            return
        self.peak_shaving_limit_w = self._manual_control_settings["peak_shaving_limit_w"]
        self.grid_charge_enabled = self._manual_control_settings["grid_charge_enabled"]
        self.grid_charge_target_soc = self._manual_control_settings["grid_charge_target_soc"]
        self.grid_charge_max_power_w = self._manual_control_settings["grid_charge_max_power_w"]

    def remember_manual_control_settings_if_allowed(self):
        if self.operating_mode != OPERATING_MODE_SMART:
            self._capture_manual_control_settings()

    def set_control_mode(self, mode: str, remember_manual=None):
        if mode not in self.control_modes:
            _LOGGER.warning("Ongeldige control_mode ontvangen: %s", mode)
            return

        if remember_manual is None:
            remember_manual = self.operating_mode != OPERATING_MODE_SMART
        if remember_manual:
            self.manual_control_mode = mode

        if mode != self.control_mode:
            _LOGGER.info("Control mode gewijzigd van '%s' naar '%s'", self.control_mode, mode)
            self.control_mode = mode
            async_dispatcher_send(self.hass, "ctrl_next_update")

    def get_control_mode(self) -> str:
        return self.control_mode

    def set_grid_charge_enabled(self, enabled: bool):
        self.grid_charge_enabled = enabled
        if self.operating_mode != OPERATING_MODE_SMART:
            self._capture_manual_control_settings()
        async_dispatcher_send(self.hass, "ctrl_next_update")

    def get_grid_charge_enabled(self) -> bool:
        return self.grid_charge_enabled

    def _get_mode_import_limit(self):
        if self.control_mode == CONTROL_MODE_PEAK_SHAVING:
            return self.peak_shaving_limit_w
        return 0.0

    def _get_grid_charge_target_soc(self):
        return max(0.0, min(self.grid_charge_target_soc, _SOC_MAX_CHARGE))

    def _get_effective_grid_charge_settings(self):
        if self.operating_mode == OPERATING_MODE_SMART:
            return (
                bool(self.smart_active_profile.get("grid_charge_enabled", False)),
                max(0.0, min(float(self.smart_active_profile.get("grid_charge_target_soc", 0.0)), _SOC_MAX_CHARGE)),
                max(float(self.smart_active_profile.get("grid_charge_max_power_w", 0.0)), 0.0),
            )

        return (
            self.grid_charge_enabled,
            self._get_grid_charge_target_soc(),
            max(self.grid_charge_max_power_w, 0.0),
        )

    def _get_grid_charge_request(self, huisverbruik, soc):
        grid_charge_enabled, target_soc, max_grid_charge_power_w = self._get_effective_grid_charge_settings()
        if not grid_charge_enabled:
            return 0.0

        if not any(soc[idx] < target_soc for idx in ["1", "2"]):
            return 0.0

        grid_headroom = max(self._get_mode_import_limit() - max(huisverbruik, 0.0), 0.0)
        return min(grid_headroom, max_grid_charge_power_w)

    def _get_regel_huisverbruik(self, huisverbruik):
        if self.control_mode != CONTROL_MODE_PEAK_SHAVING:
            return huisverbruik

        # In peak-shaving modus ontladen we alleen boven de piekgrens.
        if huisverbruik > self.peak_shaving_limit_w:
            return huisverbruik - self.peak_shaving_limit_w

        return min(huisverbruik, 0.0)

    async def _get_p1_actual_power(self):
        if not self._p1_http_url:
            value = self._get_float_state(self.config.get("p1_sensor"))
            self.p1_used_value = value
            return value

        try:
            async with self._http_session.get(self._p1_http_url, timeout=_P1_HTTP_TIMEOUT_SECONDS) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
                value = float(payload["active_power_w"])
                self.p1_used_value = value
                return value
        except (ClientError, ValueError, TypeError, KeyError):
            now = time.monotonic()
            if now - self._last_http_error_log >= 30:
                _LOGGER.warning(
                    "HTTP polling van P1 mislukt, fallback naar HA sensor '%s'",
                    self.config.get("p1_sensor"),
                )
                self._last_http_error_log = now
            value = self._get_float_state(self.config.get("p1_sensor"))
            self.p1_used_value = value
            return value

    async def _call_entity_service(self, domain, service, entity_id, service_data=None):
        if not entity_id:
            return

        payload = {"entity_id": entity_id}
        if service_data:
            payload.update(service_data)

        await self.hass.services.async_call(domain, service, payload, blocking=True)

    async def _set_select_option(self, entity_id, option, force=False):
        if not entity_id:
            _LOGGER.warning("Select-option overgeslagen: lege entity_id voor optie '%s'", option)
            return

        current_state = self.hass.states.get(entity_id)
        if not force and current_state and current_state.state == option:
            return
        await self._call_entity_service("select", "select_option", entity_id, {"option": option})

    async def _set_number_value(self, entity_id, value):
        if not entity_id:
            return

        current_state = self.hass.states.get(entity_id)
        if current_state and current_state.state not in ["unknown", "unavailable"]:
            try:
                if abs(float(current_state.state) - value) < 0.5:
                    return
            except ValueError:
                pass

        await self._call_entity_service("number", "set_value", entity_id, {"value": value})

    async def _set_switch_state(self, entity_id, turn_on):
        if not entity_id:
            return

        current_state = self.hass.states.get(entity_id)
        desired_state = "on" if turn_on else "off"
        if current_state and current_state.state == desired_state:
            return

        service = "turn_on" if turn_on else "turn_off"
        await self._call_entity_service("switch", service, entity_id)

    async def _apply_battery_command(self, bat_idx, mode, abs_power):
        entities = self._get_battery_entities(bat_idx)

        async with self._service_lock:
            await self._set_switch_state(entities["modbus_switch"], True)

            if mode == _FORCE_MODE_CHARGE:
                await self._set_number_value(entities["discharge"], 0.0)
                await self._set_number_value(entities["charge"], abs_power)
            elif mode == _FORCE_MODE_DISCHARGE:
                await self._set_number_value(entities["charge"], 0.0)
                await self._set_number_value(entities["discharge"], abs_power)
            else:
                await self._set_number_value(entities["charge"], 0.0)
                await self._set_number_value(entities["discharge"], 0.0)

            await self._set_select_option(entities["force_mode"], mode)

    async def _set_battery_failsafe(self, bat_idx, reason):
        entities = self._get_battery_entities(bat_idx)
        work_mode_entity = entities["work_mode"]

        _LOGGER.warning("Failsafe gestart voor batterij %s (%s)", bat_idx, reason)
        _LOGGER.warning(
            "Failsafe batterij %s: target work_mode=%s",
            bat_idx,
            _WORK_MODE_ANTI_FEED,
        )

        async with self._service_lock:
            before_work_mode = self.hass.states.get(work_mode_entity)
            _LOGGER.warning(
                "Failsafe batterij %s BEFORE: work_mode=%s",
                bat_idx,
                before_work_mode.state if before_work_mode else "onbekend",
            )

            # Forceer de service-call zodat een mogelijk stale HA-state de call niet blokkeert.
            await self._set_number_value(entities["charge"], 0.0)
            await self._set_number_value(entities["discharge"], 0.0)
            await self._set_select_option(entities["force_mode"], _FORCE_MODE_STOP, force=True)
            await self._set_select_option(work_mode_entity, _WORK_MODE_ANTI_FEED, force=True)

            await asyncio.sleep(0.25)

            after_work_mode = self.hass.states.get(work_mode_entity)
            _LOGGER.warning(
                "Failsafe batterij %s AFTER: work_mode=%s",
                bat_idx,
                after_work_mode.state if after_work_mode else "onbekend",
            )

        self.virtual_bat_power[bat_idx] = 0.0
        self.last_mode[bat_idx] = _FORCE_MODE_STOP
        self.last_power[bat_idx] = 0.0
        _LOGGER.warning("Batterij %s naar Anti-Feed teruggezet (%s)", bat_idx, reason)

    async def _set_all_batteries_failsafe(self, reason):
        for bat_idx in ["1", "2"]:
            try:
                await self._set_battery_failsafe(bat_idx, reason)
            except Exception:
                _LOGGER.exception("Failsafe mislukt voor batterij %s", bat_idx)

        self.p1_used_value = self._get_float_state(self.config.get("p1_sensor"))
        async_dispatcher_send(self.hass, "ctrl_next_update")

    def _empty_plan(self):
        return {
            "summary": "Nog geen Smart-plan berekend.",
            "target_soc_morning": 0,
            "target_soc_evening": 0,
            "target_soc_after_super_dal": 0,
            "grid_charge_needed_kwh": 0,
            "planned_grid_charge_power_w": 0,
            "planned_grid_charge_kwh": 0,
            "current_headroom_w": 0,
            "expected_min_soc": 0,
            "free_surplus_kwh": 0,
            "morning_need_kwh": 0,
            "evening_need_kwh": 0,
            "day_charge_potential_kwh": 0,
            "timestamps": [],
            "expected_soc": [],
            "expected_load_w": [],
            "expected_solar_w": [],
            "expected_import_w": [],
            "mode": [],
            "reasons": [],
            "control_mode": [],
            "peak_shaving_limit_w": [],
            "grid_charge_enabled": [],
            "grid_charge_target_soc": [],
            "grid_charge_max_power_w": [],
            "min_discharge_soc": [],
            "scenario": [],
            "profile_quality": "nog niet berekend",
            "generated_at": None,
        }

    def _empty_smart_profile(self):
        return {
            "timestamp": None,
            "scenario": "nog niet berekend",
            "control_mode": CONTROL_MODE_PEAK_SHAVING,
            "peak_shaving_limit_w": self.planner_import_limit_w,
            "grid_charge_enabled": False,
            "grid_charge_target_soc": 0.0,
            "grid_charge_max_power_w": 0.0,
            "min_discharge_soc": self.planner_min_reserve_soc,
            "period": None,
        }

    def _get_average_soc(self, soc=None):
        soc = soc or {
            "1": self._get_float_state(self.config.get(CONF_BATTERY_1_SOC)),
            "2": self._get_float_state(self.config.get(CONF_BATTERY_2_SOC)),
        }
        return (soc["1"] + soc["2"]) / 2.0

    def _get_total_capacity_kwh(self):
        return max(self.planner_battery_nominal_kwh_each * self.planner_battery_count, 0.1)

    def _get_float_config(self, key, default):
        try:
            return float(self.config.get(key, default))
        except (TypeError, ValueError):
            return float(default)

    def _get_datetime_state(self, entity_id):
        state = self.hass.states.get(entity_id)
        if not state or state.state in ["unknown", "unavailable", ""]:
            return None
        try:
            return datetime.fromisoformat(state.state)
        except ValueError:
            return None

    async def _get_load_profile(self):
        fallback = max(self.huisverbruik_value, self._get_float_state(self.config.get(CONF_P1_SENSOR)), 300.0)
        buckets_same_weekday = [[] for _ in range(96)]
        buckets_all = [[] for _ in range(96)]
        entity_ids = [
            "sensor.ctrl_next_hems_systeem_hems_huisverbruik_vermogen",
            "sensor.hems_huisverbruik_vermogen",
            self.config.get(CONF_P1_SENSOR),
        ]
        end = datetime.now().astimezone()
        start = end - timedelta(days=14)
        target_weekday = (end + timedelta(days=1)).weekday()

        try:
            from homeassistant.components.recorder import history as recorder_history

            for entity_id in [entity for entity in entity_ids if entity]:
                try:
                    getter = partial(
                        recorder_history.get_significant_states,
                        self.hass,
                        start,
                        end,
                        [entity_id],
                        None,
                        False,
                        False,
                        False,
                        True,
                    )
                    states_by_entity = await self.hass.async_add_executor_job(getter)
                except TypeError:
                    getter = partial(
                        recorder_history.get_significant_states,
                        self.hass,
                        start,
                        end,
                        [entity_id],
                        None,
                        False,
                        False,
                        False,
                    )
                    states_by_entity = await self.hass.async_add_executor_job(getter)
                states = states_by_entity.get(entity_id, []) if states_by_entity else []
                for item in states:
                    state_value = getattr(item, "state", None)
                    changed = getattr(item, "last_updated", None) or getattr(item, "last_changed", None)
                    if state_value in [None, "unknown", "unavailable"] or changed is None:
                        continue
                    try:
                        value = max(float(state_value), 0.0)
                    except (TypeError, ValueError):
                        continue
                    idx = changed.hour * 4 + changed.minute // 15
                    buckets_all[idx].append(value)
                    if changed.weekday() == target_weekday:
                        buckets_same_weekday[idx].append(value)
                if any(buckets_same_weekday) or any(buckets_all):
                    break
        except Exception:
            _LOGGER.debug("Recorder history niet beschikbaar voor plannerprofiel", exc_info=True)

        profile = []
        quality = "fallback huidig verbruik"
        for idx in range(96):
            values = buckets_same_weekday[idx] or buckets_all[idx]
            if values:
                profile.append(sum(values) / len(values))
                quality = "history"
            else:
                profile.append(fallback)
        return profile, quality

    async def _refresh_smart_plan(self, force=False):
        now = datetime.now().astimezone()
        if (
            not force
            and self._last_plan_refresh is not None
            and (now - self._last_plan_refresh) < timedelta(minutes=15)
        ):
            return

        load_profile, profile_quality = await self._get_load_profile()
        soc = {
            "1": self._get_float_state(self.config.get(CONF_BATTERY_1_SOC)),
            "2": self._get_float_state(self.config.get(CONF_BATTERY_2_SOC)),
        }
        inputs = PlannerInputs(
            now=now,
            current_soc_pct=self._get_average_soc(soc),
            battery_nominal_kwh_each=self.planner_battery_nominal_kwh_each,
            battery_count=int(self.planner_battery_count),
            min_reserve_soc_pct=self.planner_min_reserve_soc,
            safety_margin_pct=self.planner_safety_margin_pct,
            import_limit_w=self.planner_import_limit_w,
            max_grid_charge_power_w=self.grid_charge_max_power_w,
            forecast_remaining_today_kwh=self._get_float_state(self.config.get(CONF_FORECAST_SOLAR_REMAINING_TODAY)),
            forecast_tomorrow_kwh=self._get_float_state(self.config.get(CONF_FORECAST_SOLAR_TOMORROW)),
            forecast_peak_today=self._get_datetime_state(self.config.get(CONF_FORECAST_SOLAR_PEAK_TODAY)),
            forecast_peak_tomorrow=self._get_datetime_state(self.config.get(CONF_FORECAST_SOLAR_PEAK_TOMORROW)),
            load_profile_w=load_profile,
        )
        self.smart_plan = build_plan(inputs)
        self.smart_plan["profile_quality"] = profile_quality
        self.smart_plan["generated_at"] = now.isoformat()
        self._last_plan_refresh = now
        self.smart_active_profile = self._get_current_smart_profile(now)
        async_dispatcher_send(self.hass, _SMART_PLAN_DISPATCH)

    async def _send_plan_notification_if_needed(self):
        now = datetime.now().astimezone()
        if now.hour != 21 or self._last_plan_notification_date == now.date():
            return

        await self._refresh_smart_plan(force=True)
        service_name = self.config.get(CONF_PLANNER_NOTIFY_SERVICE, DEFAULT_PLANNER_NOTIFY_SERVICE)
        if "." not in service_name:
            return
        domain, service = service_name.split(".", 1)
        dashboard_path = self.config.get(CONF_PLANNER_DASHBOARD_PATH, DEFAULT_PLANNER_DASHBOARD_PATH)
        message = (
            f"{self.smart_plan['summary']} "
            f"Ochtend {self.smart_plan['target_soc_morning']:.0f}%, "
            f"avond {self.smart_plan['target_soc_evening']:.0f}%, "
            f"superdal {self.smart_plan['grid_charge_needed_kwh']:.2f} kWh."
        )
        await self.hass.services.async_call(
            domain,
            service,
            {
                "title": "HEMS Smart planning",
                "message": message,
                "data": {
                    "url": dashboard_path,
                    "clickAction": dashboard_path,
                    "tag": "hems_smart_plan",
                    "group": "hems",
                },
            },
            blocking=False,
        )
        self._last_plan_notification_date = now.date()

    async def _apply_control_cycle(
        self,
        control_power,
        huisverbruik,
        regel_huisverbruik,
        grid_charge_request,
        soc,
        min_discharge_soc,
        charge_target_soc,
    ):
        self._filtered_huisverbruik = (
            (1.0 - self.filter_alpha) * self._filtered_huisverbruik
            + self.filter_alpha * control_power
        )

        filtered_abs = abs(self._filtered_huisverbruik)
        stop_threshold = self.deadband
        start_threshold = self.deadband + self.deadband_release_margin

        if self._global_mode == _FORCE_MODE_STOP:
            if filtered_abs <= start_threshold:
                global_mode = _FORCE_MODE_STOP
            elif self._filtered_huisverbruik > 0:
                global_mode = _FORCE_MODE_DISCHARGE
            else:
                global_mode = _FORCE_MODE_CHARGE
        else:
            if filtered_abs <= stop_threshold:
                global_mode = _FORCE_MODE_STOP
            elif self._filtered_huisverbruik > 0:
                global_mode = _FORCE_MODE_DISCHARGE
            else:
                global_mode = _FORCE_MODE_CHARGE

        now_monotonic = time.monotonic()
        if (
            global_mode != self._global_mode
            and (now_monotonic - self._last_global_mode_change) < self.min_mode_hold_seconds
        ):
            global_mode = self._global_mode

        if global_mode != self._global_mode:
            self._global_mode = global_mode
            self._last_global_mode_change = now_monotonic

        if global_mode == _FORCE_MODE_DISCHARGE:
            available = [idx for idx in ["1", "2"] if soc[idx] > min_discharge_soc]
        elif global_mode == _FORCE_MODE_CHARGE:
            available = [idx for idx in ["1", "2"] if soc[idx] < charge_target_soc]
        else:
            available = []

        if available:
            target_power_per_bat = min(
                abs(self._filtered_huisverbruik) / len(available),
                self.max_power_per_bat,
            )
            if 0.0 < target_power_per_bat < self.min_power_per_bat:
                target_power_per_bat = self.min_power_per_bat
        else:
            target_power_per_bat = 0.0

        for bat_idx in ["1", "2"]:
            if bat_idx in available:
                mode = global_mode
                prev_abs = self.last_power[bat_idx] if self.last_mode[bat_idx] == mode else 0.0
                delta = target_power_per_bat - prev_abs
                if abs(delta) > self.max_power_step_per_cycle:
                    abs_gewenst = prev_abs + (self.max_power_step_per_cycle if delta > 0 else -self.max_power_step_per_cycle)
                else:
                    abs_gewenst = target_power_per_bat
                v_val = abs_gewenst if mode == _FORCE_MODE_DISCHARGE else -abs_gewenst
            else:
                mode = _FORCE_MODE_STOP
                prev_abs = self.last_power[bat_idx] if self.last_mode[bat_idx] == _FORCE_MODE_STOP else 0.0
                delta = -prev_abs
                if abs(delta) > self.max_power_step_per_cycle:
                    abs_gewenst = prev_abs - self.max_power_step_per_cycle
                else:
                    abs_gewenst = 0.0
                v_val = 0.0

            if self.last_mode[bat_idx] != mode or abs(self.last_power[bat_idx] - abs_gewenst) >= self.cache_threshold:
                await self._apply_battery_command(bat_idx, mode, abs_gewenst)
                self.virtual_bat_power[bat_idx] = v_val
                self.last_mode[bat_idx] = mode
                self.last_power[bat_idx] = abs_gewenst

                _LOGGER.info(
                    "[CTRL-NEXT] Bat %s update: bedrijfsmodus=%s regeling=%s huis=%.0fW regel=%.0fW netladen=%.0fW filtered=%.0fW SoC=%.1f%% actie=%s %.0fW",
                    bat_idx,
                    self.operating_mode,
                    self.control_mode,
                    huisverbruik,
                    regel_huisverbruik,
                    grid_charge_request,
                    self._filtered_huisverbruik,
                    soc[bat_idx],
                    mode,
                    abs_gewenst,
                )

        async_dispatcher_send(self.hass, "ctrl_next_update")

    async def _collect_power_state(self):
        p1_actual = await self._get_p1_actual_power()
        bat1_ac = self._get_float_state(self.config.get(CONF_BAT1_AC_POWER))
        bat2_ac = self._get_float_state(self.config.get(CONF_BAT2_AC_POWER))
        huisverbruik = p1_actual + bat1_ac + bat2_ac
        self.huisverbruik_value = huisverbruik
        soc = {
            "1": self._get_float_state(self.config.get(CONF_BATTERY_1_SOC)),
            "2": self._get_float_state(self.config.get(CONF_BATTERY_2_SOC)),
        }
        return p1_actual, huisverbruik, soc

    async def _run_manual_cycle(self):
        _, huisverbruik, soc = await self._collect_power_state()
        regel_huisverbruik = self._get_regel_huisverbruik(huisverbruik)
        grid_charge_request = self._get_grid_charge_request(huisverbruik, soc)
        control_power = regel_huisverbruik - grid_charge_request
        charge_target = self._get_grid_charge_target_soc() if self.grid_charge_enabled else _SOC_MAX_CHARGE
        await self._apply_control_cycle(
            control_power,
            huisverbruik,
            regel_huisverbruik,
            grid_charge_request,
            soc,
            _SOC_MIN_DISCHARGE,
            charge_target,
        )

    def _smart_min_discharge_soc(self):
        return self.smart_active_profile.get("min_discharge_soc", self.planner_min_reserve_soc)

    def _get_plan_value(self, key, idx, default):
        values = self.smart_plan.get(key, [])
        if idx < len(values):
            return values[idx]
        return default

    def _get_current_smart_profile(self, now=None):
        now = now or datetime.now().astimezone()
        timestamps = self.smart_plan.get("timestamps", [])
        if not timestamps:
            return self._empty_smart_profile()

        selected_idx = 0
        for idx, value in enumerate(timestamps):
            try:
                ts = datetime.fromisoformat(value)
            except (TypeError, ValueError):
                continue
            if ts <= now:
                selected_idx = idx
            else:
                break

        return {
            "timestamp": self._get_plan_value("timestamps", selected_idx, None),
            "scenario": self._get_plan_value("scenario", selected_idx, "hold_reserve"),
            "control_mode": self._get_plan_value("control_mode", selected_idx, CONTROL_MODE_PEAK_SHAVING),
            "peak_shaving_limit_w": float(self._get_plan_value("peak_shaving_limit_w", selected_idx, self.planner_import_limit_w)),
            "grid_charge_enabled": bool(self._get_plan_value("grid_charge_enabled", selected_idx, False)),
            "grid_charge_target_soc": float(self._get_plan_value("grid_charge_target_soc", selected_idx, 0.0)),
            "grid_charge_max_power_w": float(self._get_plan_value("grid_charge_max_power_w", selected_idx, 0.0)),
            "min_discharge_soc": float(self._get_plan_value("min_discharge_soc", selected_idx, self.planner_min_reserve_soc)),
            "period": self._get_plan_value("mode", selected_idx, None),
        }

    def _set_smart_active_profile(self, profile):
        if profile == self.smart_active_profile:
            return
        self.smart_active_profile = profile
        async_dispatcher_send(self.hass, _SMART_PLAN_DISPATCH)

    def _apply_smart_profile_settings(self, profile):
        self.set_control_mode(profile["control_mode"], remember_manual=False)
        self.peak_shaving_limit_w = profile["peak_shaving_limit_w"]

    async def _run_smart_cycle(self):
        await self._refresh_smart_plan(force=False)
        await self._send_plan_notification_if_needed()
        _, huisverbruik, soc = await self._collect_power_state()

        now = datetime.now().astimezone()
        profile = self._get_current_smart_profile(now)
        self._set_smart_active_profile(profile)
        self._apply_smart_profile_settings(profile)

        min_discharge_soc = self._smart_min_discharge_soc()
        regel_huisverbruik = self._get_regel_huisverbruik(huisverbruik)
        grid_charge_request = self._get_grid_charge_request(huisverbruik, soc)
        control_power = regel_huisverbruik - grid_charge_request

        charge_target_soc = _SOC_MAX_CHARGE
        if profile["grid_charge_enabled"]:
            charge_target_soc = profile["grid_charge_target_soc"]

        await self._apply_control_cycle(
            control_power,
            huisverbruik,
            regel_huisverbruik,
            grid_charge_request,
            soc,
            min_discharge_soc,
            charge_target_soc,
        )

    async def _loop(self):
        while self.running:
            try:
                await self._refresh_smart_plan(force=False)
                await self._send_plan_notification_if_needed()

                if self.operating_mode == OPERATING_MODE_OFF:
                    await asyncio.sleep(1)
                    continue
                if self.operating_mode == OPERATING_MODE_SMART:
                    await self._run_smart_cycle()
                else:
                    await self._run_manual_cycle()
            except Exception:
                _LOGGER.exception("Fout in controller loop; failsafe wordt geactiveerd")
                await self.set_operating_mode(OPERATING_MODE_OFF)

            await asyncio.sleep(1)

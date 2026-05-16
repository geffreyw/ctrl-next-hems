import asyncio
import logging
import time

from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send # NIEUW
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import (
    CONF_BAT1_CHARGE,
    CONF_BAT1_DISCHARGE,
    CONF_BAT1_FORCE_MODE,
    CONF_BAT1_MODBUS_SWITCH,
    CONF_BAT1_WORK_MODE,
    CONF_BAT2_CHARGE,
    CONF_BAT2_DISCHARGE,
    CONF_BAT2_FORCE_MODE,
    CONF_BAT2_MODBUS_SWITCH,
    CONF_BAT2_WORK_MODE,
    CONF_BATTERY_1_SOC,
    CONF_BATTERY_2_SOC,
    CONF_CONTROL_MODE,
    CONTROL_MODE_ANTI_FEED,
    CONTROL_MODE_PEAK_SHAVING,
    CONF_P1_HTTP_JSON_KEY,
    CONF_P1_HTTP_TIMEOUT,
    CONF_P1_HTTP_URL,
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

class CtrlNextController:
    def __init__(self, hass: HomeAssistant, config_data: dict):
        self.hass = hass
        self.config = config_data
        self.running = False
        self.enabled = True
        self._task = None
        
        self.virtual_bat_power = {"1": 0.0, "2": 0.0}
        self.p1_used_value = 0.0
        self.huisverbruik_value = 0.0

        self._http_session = async_get_clientsession(hass)
        self._p1_http_url = (self.config.get(CONF_P1_HTTP_URL) or "").strip()
        self._p1_http_json_key = (self.config.get(CONF_P1_HTTP_JSON_KEY) or "power").strip()
        self._p1_http_timeout = float(self.config.get(CONF_P1_HTTP_TIMEOUT, 2.0))
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

        self.max_power_per_bat = 2500.0

        # Regelparameters (configureerbaar via number-entities).
        self.peak_shaving_limit_w = _DEFAULT_PEAK_SHAVING_LIMIT_W
        self.grid_charge_enabled = False
        self.grid_charge_target_soc = _DEFAULT_GRID_CHARGE_TARGET_SOC
        self.grid_charge_max_power_w = _DEFAULT_GRID_CHARGE_MAX_POWER_W
        self.deadband = 15.0 
        self.cache_threshold = 25.0

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

    async def set_enabled(self, status: bool):
        self.enabled = status
        if status:
            self.last_mode = {"1": "Unknown", "2": "Unknown"}
            self.last_power = {"1": -1.0, "2": -1.0}
            return

        await self._set_all_batteries_failsafe("controller uitgeschakeld")

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

    def _extract_json_value(self, payload):
        # Ondersteunt een geneste key zoals "data.power"
        value = payload
        if self._p1_http_json_key:
            for part in self._p1_http_json_key.split("."):
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    raise ValueError(f"JSON key '{self._p1_http_json_key}' niet gevonden")
        return float(value)

    def set_control_mode(self, mode: str):
        if mode not in self.control_modes:
            _LOGGER.warning("Ongeldige control_mode ontvangen: %s", mode)
            return

        if mode != self.control_mode:
            _LOGGER.info("Control mode gewijzigd van '%s' naar '%s'", self.control_mode, mode)
            self.control_mode = mode

    def get_control_mode(self) -> str:
        return self.control_mode

    def set_grid_charge_enabled(self, enabled: bool):
        self.grid_charge_enabled = enabled

    def get_grid_charge_enabled(self) -> bool:
        return self.grid_charge_enabled

    def _get_mode_import_limit(self):
        if self.control_mode == CONTROL_MODE_PEAK_SHAVING:
            return self.peak_shaving_limit_w
        return 0.0

    def _get_grid_charge_target_soc(self):
        return max(0.0, min(self.grid_charge_target_soc, _SOC_MAX_CHARGE))

    def _get_grid_charge_request(self, huisverbruik, soc):
        if not self.grid_charge_enabled:
            return 0.0

        target_soc = self._get_grid_charge_target_soc()
        if not any(soc[idx] < target_soc for idx in ["1", "2"]):
            return 0.0

        grid_headroom = max(self._get_mode_import_limit() - max(huisverbruik, 0.0), 0.0)
        return min(grid_headroom, self.grid_charge_max_power_w)

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
            timeout = max(0.1, self._p1_http_timeout)
            async with self._http_session.get(self._p1_http_url, timeout=timeout) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
                value = self._extract_json_value(payload)
                self.p1_used_value = value
                return value
        except (ClientError, ValueError, TypeError):
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

    async def _loop(self):
        while self.running:
            if self.enabled:
                try:
                    p1_actual = await self._get_p1_actual_power()
                    bat1_ac = self._get_float_state(self.config.get("bat1_ac_power"))
                    bat2_ac = self._get_float_state(self.config.get("bat2_ac_power"))
                    
                    huisverbruik = p1_actual + bat1_ac + bat2_ac
                    self.huisverbruik_value = huisverbruik
                    regel_huisverbruik = self._get_regel_huisverbruik(huisverbruik)

                    soc = {
                        "1": self._get_float_state(self.config.get(CONF_BATTERY_1_SOC)),
                        "2": self._get_float_state(self.config.get(CONF_BATTERY_2_SOC)),
                    }
                    grid_charge_request = self._get_grid_charge_request(huisverbruik, soc)
                    control_power = regel_huisverbruik - grid_charge_request

                    # Low-pass filter dempt spikes in meting en maakt de regeling rustiger.
                    self._filtered_huisverbruik = (
                        (1.0 - self.filter_alpha) * self._filtered_huisverbruik
                        + self.filter_alpha * control_power
                    )

                    # Hysterese voorkomt flippen rond 0W; hold voorkomt snelle modewissels.
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

                    now = time.monotonic()
                    if (
                        global_mode != self._global_mode
                        and (now - self._last_global_mode_change) < self.min_mode_hold_seconds
                    ):
                        global_mode = self._global_mode

                    if global_mode != self._global_mode:
                        self._global_mode = global_mode
                        self._last_global_mode_change = now

                    # Bepaal welke batterijen beschikbaar zijn voor de gewenste mode
                    if global_mode == _FORCE_MODE_DISCHARGE:
                        available = [idx for idx in ["1", "2"] if soc[idx] > _SOC_MIN_DISCHARGE]
                    elif global_mode == _FORCE_MODE_CHARGE:
                        target_soc = self._get_grid_charge_target_soc()
                        if self.grid_charge_enabled:
                            available = [idx for idx in ["1", "2"] if soc[idx] < target_soc]
                        else:
                            available = [idx for idx in ["1", "2"] if soc[idx] < _SOC_MAX_CHARGE]
                    else:
                        available = []

                    # Verdeel het totale gevraagde vermogen over de beschikbare batterijen
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
                                "[CTRL-NEXT] Bat %s update: Huisverbruik=%.0fW (regel=%.0fW, netladen=%.0fW, filtered=%.0fW) SoC=%.1f%% | Actie: %s met %.0fW",
                                bat_idx,
                                huisverbruik,
                                regel_huisverbruik,
                                grid_charge_request,
                                self._filtered_huisverbruik,
                                soc[bat_idx],
                                mode,
                                abs_gewenst,
                            )

                    # Stuur een signaal naar de sensoren om te verversen in de UI
                    async_dispatcher_send(self.hass, "ctrl_next_update")
                    
                except Exception:
                    _LOGGER.exception("Fout in controller loop; failsafe wordt geactiveerd")
                    self.enabled = False
                    await self._set_all_batteries_failsafe("controller fout")
            
            await asyncio.sleep(1)

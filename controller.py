import asyncio
import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send # NIEUW

_LOGGER = logging.getLogger(__name__)

class CtrlNextController:
    def __init__(self, hass: HomeAssistant, config_data: dict):
        self.hass = hass
        self.config = config_data
        self.running = False
        self.enabled = True
        self._task = None
        
        self.virtual_bat_power = {"1": 0.0, "2": 0.0}
        self.virtual_p1_value = 0.0

        self.max_power_per_bat = 2500.0
        self.deadband = 15.0 
        self.cache_threshold = 25.0
        
        self.last_mode = {"1": "Stop", "2": "Stop"}
        self.last_power = {"1": 0.0, "2": 0.0}

    async def start(self):
        self.running = True
        self._task = self.hass.async_create_background_task(self._loop(), "CTRL-NEXT HEMS Loop")

    async def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()

    async def set_enabled(self, status: bool):
        self.enabled = status

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

    async def _loop(self):
        while self.running:
            if self.enabled:
                try:
                    p1_actual = self._get_float_state(self.config.get("p1_sensor"))
                    bat1_ac = self._get_float_state(self.config.get("bat1_ac_power"))
                    bat2_ac = self._get_float_state(self.config.get("bat2_ac_power"))
                    
                    huisverbruik = p1_actual + bat1_ac + bat2_ac
                    doel_per_bat = huisverbruik / 2
                    
                    for bat_idx in ["1", "2"]:
                        abs_gewenst = 0.0
                        mode = "Stop"
                        v_val = 0.0

                        if abs(doel_per_bat) > self.deadband:
                            abs_gewenst = min(abs(doel_per_bat), self.max_power_per_bat)
                            if doel_per_bat > 0:
                                mode = "Discharge"
                                v_val = abs_gewenst
                            else:
                                mode = "Charge"
                                v_val = -abs_gewenst

                        # Check of we de drempelwaarde voorbij zijn
                        if self.last_mode[bat_idx] != mode or abs(self.last_power[bat_idx] - abs_gewenst) >= self.cache_threshold:
                            self.virtual_bat_power[bat_idx] = v_val
                            self.last_mode[bat_idx] = mode
                            self.last_power[bat_idx] = abs_gewenst
                            
                            # --- NIEUWE LOGGING ---
                            _LOGGER.info(
                                f"[CTRL-NEXT SIMULATIE] Bat {bat_idx} update: Huisverbruik={huisverbruik:.0f}W "
                                f"| Actie: {mode} met {abs_gewenst:.0f}W"
                            )

                    self.virtual_p1_value = huisverbruik - (self.virtual_bat_power["1"] + self.virtual_bat_power["2"])
                    
                    # Stuur een signaal naar de sensoren om te verversen in de UI
                    async_dispatcher_send(self.hass, "ctrl_next_update")
                    
                except Exception as e:
                    _LOGGER.error(f"Fout in simulatie loop: {e}")
            
            await asyncio.sleep(1)
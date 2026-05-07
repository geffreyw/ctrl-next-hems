import asyncio
import logging
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

class CtrlNextHEMSController:
    def __init__(self, hass: HomeAssistant, p1_entity_id: str, bat1_soc_id: str, bat2_soc_id: str):
        self.hass = hass
        self.p1_entity_id = p1_entity_id
        self.bat1_soc_id = bat1_soc_id
        self.bat2_soc_id = bat2_soc_id
        self.running = False
        self._task = None

    async def start(self):
        """Start de loop die elke seconde draait."""
        self.running = True
        self._task = self.hass.async_create_background_task(self._loop(), "CTRL-NEXT HEMS Control Loop")
        _LOGGER.info("CTRL-NEXT HEMS Control Loop gestart.")

    async def stop(self):
        """Stop de loop netjes."""
        self.running = False
        if self._task:
            self._task.cancel()
        _LOGGER.info("CTRL-NEXT HEMS Control Loop gestopt.")

    async def _loop(self):
        """De daadwerkelijke rekenmachine (draait elke seconde)."""
        while self.running:
            try:
                # 1. Lees de P1 meter uit
                p1_state = self.hass.states.get(self.p1_entity_id)
                
                if p1_state and p1_state.state not in ["unknown", "unavailable"]:
                    p1_power = float(p1_state.state)
                    
                    # 2. Basis wiskunde (Zero-Export Proportionele Regeling)
                    # Als p1_power > 0 (We halen stroom van het net) -> Batterij moet ontladen
                    # Als p1_power < 0 (We sturen stroom naar het net) -> Batterij moet opladen
                    
                    if p1_power > 0:
                        actie = "ONTLAAD"
                        watt = p1_power
                    elif p1_power < 0:
                        actie = "LAAD"
                        watt = abs(p1_power)
                    else:
                        actie = "RUST"
                        watt = 0

                    # We printen dit voor nu alleen in de logs als waarschuwing, zodat we kunnen testen!
                    _LOGGER.warning(f"DRY RUN - P1: {p1_power}W | Advies aan batterijen: {actie} met {watt}W")
                    
            except Exception as e:
                _LOGGER.error(f"Fout in CTRL-NEXT HEMS loop: {e}")
            
            # Wacht exact 1 seconde tot de volgende cyclus
            await asyncio.sleep(1)
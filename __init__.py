import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .controller import CtrlNextController

_LOGGER = logging.getLogger(__name__)

# Voeg "select" toe aan de platforms
PLATFORMS = ["switch", "number", "sensor", "select"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    config_data = {**entry.data, **entry.options}
    controller = CtrlNextController(hass, config_data)
    hass.data[DOMAIN][entry.entry_id] = controller
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await controller.start()
    
    _LOGGER.info("CTRL-NEXT HEMS gestart met actieve Modbus-sturing")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    controller = hass.data[DOMAIN].pop(entry.entry_id)
    await controller.stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .controller import CtrlNextController

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["switch", "number", "sensor", "select", "binary_sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    config_data = {**entry.data, **entry.options}
    controller = CtrlNextController(hass, config_data)
    hass.data[DOMAIN][entry.entry_id] = controller

    async def async_disable_hems_before_stop(_event):
        _LOGGER.warning("Home Assistant stopt; CTRL-NEXT HEMS wordt uitgeschakeld")
        await controller.set_enabled(False)

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_disable_hems_before_stop)
    )
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await controller.start()
    
    _LOGGER.info("CTRL-NEXT HEMS gestart met actieve Modbus-sturing")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    controller = hass.data[DOMAIN].pop(entry.entry_id)
    await controller.stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

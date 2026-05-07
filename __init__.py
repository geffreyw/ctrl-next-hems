import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, CONF_P1_SENSOR, CONF_BATTERY_1_SOC, CONF_BATTERY_2_SOC
from .controller import CtrlNextHEMSController

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Zet de CTRL-NEXT HEMS op vanuit een config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Haal de gekozen sensoren op uit de configuratie
    p1_sensor = entry.data.get(CONF_P1_SENSOR)
    bat1_soc = entry.data.get(CONF_BATTERY_1_SOC)
    bat2_soc = entry.data.get(CONF_BATTERY_2_SOC)

    # Maak de controller aan met deze sensoren
    controller = CtrlNextHEMSController(hass, p1_sensor, bat1_soc, bat2_soc)
    
    # Sla de controller op in het geheugen van HA zodat we hem later kunnen stoppen
    hass.data[DOMAIN][entry.entry_id] = controller
    
    # Start de loop
    await controller.start()
    
    _LOGGER.info(f"CTRL-NEXT HEMS succesvol gekoppeld aan P1 meter: {p1_sensor}")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Verwijder de integratie netjes en stop de loop."""
    controller = hass.data[DOMAIN].pop(entry.entry_id)
    await controller.stop()
    _LOGGER.info("CTRL-NEXT HEMS is afgesloten.")
    return True
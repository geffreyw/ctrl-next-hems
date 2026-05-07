import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Zet de Marstek Manager op vanuit een config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Hier komt later onze opstart-logica en de achtergrondtaak (Coordinator)
    _LOGGER.info("Marstek Manager is succesvol opgestart!")
    
    # Stuur HA naar de platforms (zoals sensor.py of switch.py) die we later maken
    # await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "switch"])
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Verwijder de integratie netjes."""
    _LOGGER.info("Marstek Manager wordt afgesloten.")
    # unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "switch"])
    # if unload_ok:
    #     hass.data[DOMAIN].pop(entry.entry_id)
    return True

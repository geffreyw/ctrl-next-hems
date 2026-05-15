from homeassistant.components.select import SelectEntity
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONTROL_MODE_ANTI_FEED,
    CONTROL_MODES,
    DOMAIN,
)


async def async_setup_entry(hass, entry, async_add_entities):
    controller = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HemsControlModeSelect(controller)])


class HemsControlModeSelect(RestoreEntity, SelectEntity):
    def __init__(self, controller):
        self._controller = controller
        self._attr_name = "HEMS Regeling Modus"
        self._attr_unique_id = f"{controller.config.get('p1_sensor')}_control_mode"
        self._attr_icon = "mdi:transmission-tower-export"
        self._attr_options = CONTROL_MODES

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._controller.config.get('p1_sensor'))},
            "name": "CTRL-NEXT HEMS Systeem",
            "manufacturer": "CTRL-NEXT",
            "model": "HEMS AI Controller",
        }

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state in CONTROL_MODES:
            self._controller.set_control_mode(last_state.state)
        else:
            self._controller.set_control_mode(CONTROL_MODE_ANTI_FEED)
        self.async_write_ha_state()

    @property
    def current_option(self):
        return self._controller.get_control_mode()

    async def async_select_option(self, option: str):
        if option not in CONTROL_MODES:
            return
        self._controller.set_control_mode(option)
        self.async_write_ha_state()

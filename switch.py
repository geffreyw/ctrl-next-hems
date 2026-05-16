from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    controller = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        HemsControlSwitch(controller),
        HemsGridChargeSwitch(controller),
    ])


class HemsControlSwitch(SwitchEntity):
    def __init__(self, controller):
        self._controller = controller
        self._attr_name = "CTRL-NEXT HEMS Actief"
        self._attr_unique_id = f"{controller.config.get('p1_sensor')}_enable_switch"
        self._attr_icon = "mdi:lightning-bolt-circle"

    @property
    def device_info(self):
        """Bundel deze entiteit onder het hoofdapparaat."""
        return {
            "identifiers": {(DOMAIN, self._controller.config.get('p1_sensor'))},
            "name": "CTRL-NEXT HEMS Systeem",
            "manufacturer": "CTRL-NEXT",
            "model": "HEMS AI Controller",
        }

    @property
    def is_on(self):
        return self._controller.enabled

    async def async_turn_on(self, **kwargs):
        await self._controller.set_enabled(True)

    async def async_turn_off(self, **kwargs):
        await self._controller.set_enabled(False)


class HemsGridChargeSwitch(RestoreEntity, SwitchEntity):
    def __init__(self, controller):
        self._controller = controller
        self._attr_name = "HEMS Netladen Toestaan"
        self._attr_unique_id = f"{controller.config.get('p1_sensor')}_grid_charge_enable"
        self._attr_icon = "mdi:transmission-tower-import"

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
        if last_state:
            self._controller.set_grid_charge_enabled(last_state.state == "on")

    @property
    def is_on(self):
        return self._controller.get_grid_charge_enabled()

    async def async_turn_on(self, **kwargs):
        self._controller.set_grid_charge_enabled(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._controller.set_grid_charge_enabled(False)
        self.async_write_ha_state()
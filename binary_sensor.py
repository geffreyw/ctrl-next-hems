from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN

_SMART_PLAN_UPDATE = "ctrl_next_plan_update"


async def async_setup_entry(hass, entry, async_add_entities):
    controller = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        HemsPlanGridChargeRecommendedBinarySensor(controller),
    ])


class HemsPlanGridChargeRecommendedBinarySensor(BinarySensorEntity):
    def __init__(self, controller):
        self._controller = controller
        self._attr_name = "HEMS Plan Netladen Aanbevolen"
        self._attr_unique_id = f"{controller.config.get('p1_sensor')}_smart_plan_grid_charge_recommended"
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
        self.async_on_remove(
            async_dispatcher_connect(self.hass, _SMART_PLAN_UPDATE, self.async_write_ha_state)
        )

    @property
    def is_on(self):
        return self._controller.smart_plan.get("grid_charge_needed_kwh", 0) > 0.05

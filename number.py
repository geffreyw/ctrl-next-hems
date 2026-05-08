from homeassistant.components.number import RestoreNumber
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    controller = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        HemsParamSlider(controller, "Deadband (W)", 0, 100, "deadband", "mdi:tune-vertical"),
        HemsParamSlider(controller, "Modbus Cache Drempel (W)", 0, 200, "cache_threshold", "mdi:memory")
    ])

class HemsParamSlider(RestoreNumber):
    def __init__(self, controller, name, min_val, max_val, param_name, icon):
        self._controller = controller
        self._param_name = param_name
        self._attr_name = f"HEMS {name}"
        self._attr_native_min_value = min_val
        self._attr_native_max_value = max_val
        self._attr_native_step = 1
        self._attr_icon = icon
        self._attr_unique_id = f"{controller.config.get('p1_sensor')}_{param_name}"

    @property
    def device_info(self):
        """Bundel deze entiteit onder het hoofdapparaat."""
        return {
            "identifiers": {(DOMAIN, self._controller.config.get('p1_sensor'))},
            "name": "CTRL-NEXT HEMS Systeem",
            "manufacturer": "CTRL-NEXT",
            "model": "HEMS AI Controller",
        }

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last_number_data = await self.async_get_last_number_data()
        if last_number_data and last_number_data.native_value is not None:
            val = float(last_number_data.native_value)
            setattr(self._controller, self._param_name, val)
            self._attr_native_value = val

    @property
    def native_value(self):
        return getattr(self._controller, self._param_name)

    async def async_set_native_value(self, value):
        val = float(value)
        setattr(self._controller, self._param_name, val)
        self._attr_native_value = val
        self.async_write_ha_state()
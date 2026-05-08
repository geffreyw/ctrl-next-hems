from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfPower
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    controller = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        VirtualBatteryPowerSensor(controller, "1"),
        VirtualBatteryPowerSensor(controller, "2"),
        VirtualP1PowerSensor(controller)
    ])

class VirtualBatteryPowerSensor(SensorEntity):
    def __init__(self, controller, bat_idx):
        self._controller = controller
        self._bat_idx = bat_idx
        self._attr_name = f"HEMS Virtuele Batterij {bat_idx} Power"
        self._attr_unique_id = f"hems_virt_bat_{bat_idx}"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_state_class = SensorStateClass.MEASUREMENT

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
        self.async_on_remove(
            async_dispatcher_connect(self.hass, "ctrl_next_update", self.async_write_ha_state)
        )

    @property
    def native_value(self):
        return self._controller.virtual_bat_power[self._bat_idx]

class VirtualP1PowerSensor(SensorEntity):
    def __init__(self, controller):
        self._controller = controller
        self._attr_name = "HEMS Virtuele P1 Power"
        self._attr_unique_id = "hems_virt_p1"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_state_class = SensorStateClass.MEASUREMENT

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
        self.async_on_remove(
            async_dispatcher_connect(self.hass, "ctrl_next_update", self.async_write_ha_state)
        )

    @property
    def native_value(self):
        return self._controller.virtual_p1_value
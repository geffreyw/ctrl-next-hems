from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfPower
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    controller = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        BatteryPowerSensor(controller, "1"),
        BatteryPowerSensor(controller, "2"),
        P1UsedPowerSensor(controller),
        HuisverbruikPowerSensor(controller),
    ])

class BatteryPowerSensor(SensorEntity):
    def __init__(self, controller, bat_idx):
        self._controller = controller
        self._bat_idx = bat_idx
        self._attr_name = f"HEMS Batterij {bat_idx} Vermogen"
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


class P1UsedPowerSensor(SensorEntity):
    def __init__(self, controller):
        self._controller = controller
        self._attr_name = "HEMS P1 Vermogen Gebruikt"
        self._attr_unique_id = "hems_p1_used_power"
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
        return self._controller.p1_used_value


class HuisverbruikPowerSensor(SensorEntity):
    def __init__(self, controller):
        self._controller = controller
        self._attr_name = "HEMS Huisverbruik Vermogen"
        self._attr_unique_id = "hems_huisverbruik_power"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_state_class = SensorStateClass.MEASUREMENT

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
            async_dispatcher_connect(self.hass, "ctrl_next_update", self.async_write_ha_state)
        )

    @property
    def native_value(self):
        return self._controller.huisverbruik_value
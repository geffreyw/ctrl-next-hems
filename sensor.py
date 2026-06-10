from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .const import DOMAIN

_CTRL_NEXT_UPDATE = "ctrl_next_update"
_SMART_PLAN_UPDATE = "ctrl_next_plan_update"


async def async_setup_entry(hass, entry, async_add_entities):
    controller = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        BatteryPowerSensor(controller, "1"),
        BatteryPowerSensor(controller, "2"),
        P1UsedPowerSensor(controller),
        HuisverbruikPowerSensor(controller),
        AverageBatterySocSensor(controller),
        BatteryTotalCapacitySensor(controller),
        BatteryUsableAboveReserveSensor(controller),
        CurrentBatteryEnergySensor(controller),
        LiveImportHeadroomSensor(controller),
        PlanSummarySensor(controller),
        PlanMetricSensor(controller, "HEMS Plan Doel SoC Ochtendpiek", "target_soc_morning", PERCENTAGE, "mdi:battery-clock", SensorDeviceClass.BATTERY),
        PlanMetricSensor(controller, "HEMS Plan Doel SoC Avondpiek", "target_soc_evening", PERCENTAGE, "mdi:battery-clock", SensorDeviceClass.BATTERY),
        PlanMetricSensor(controller, "HEMS Plan Doel SoC Na Superdal", "target_soc_after_super_dal", PERCENTAGE, "mdi:battery-charging-80", SensorDeviceClass.BATTERY),
        PlanMetricSensor(controller, "HEMS Plan Superdal Laden Nodig", "grid_charge_needed_kwh", UnitOfEnergy.KILO_WATT_HOUR, "mdi:transmission-tower-import", SensorDeviceClass.ENERGY),
        PlanMetricSensor(controller, "HEMS Plan Gepland Netlaadvermogen", "planned_grid_charge_power_w", UnitOfPower.WATT, "mdi:ev-station", SensorDeviceClass.POWER),
        PlanMetricSensor(controller, "HEMS Plan Import Headroom", "current_headroom_w", UnitOfPower.WATT, "mdi:gauge", SensorDeviceClass.POWER),
        PlanMetricSensor(controller, "HEMS Plan Verwachte Minimum SoC", "expected_min_soc", PERCENTAGE, "mdi:battery-alert-variant-outline", SensorDeviceClass.BATTERY),
        PlanMetricSensor(controller, "HEMS Plan Batterijoverschot Vrij", "free_surplus_kwh", UnitOfEnergy.KILO_WATT_HOUR, "mdi:battery-plus", SensorDeviceClass.ENERGY),
        PlanMetricSensor(controller, "HEMS Plan Ochtendpiek Energie", "morning_need_kwh", UnitOfEnergy.KILO_WATT_HOUR, "mdi:weather-sunset-up", SensorDeviceClass.ENERGY),
        PlanMetricSensor(controller, "HEMS Plan Avondpiek Energie", "evening_need_kwh", UnitOfEnergy.KILO_WATT_HOUR, "mdi:weather-sunset-down", SensorDeviceClass.ENERGY),
        PlanMetricSensor(controller, "HEMS Plan Dag Solar Laadpotentieel", "day_charge_potential_kwh", UnitOfEnergy.KILO_WATT_HOUR, "mdi:solar-power-variant", SensorDeviceClass.ENERGY),
        PlanTextSensor(controller, "HEMS Plan Profielkwaliteit", "profile_quality", "mdi:database-clock-outline"),
        PlanTextSensor(controller, "HEMS Plan Laatste Berekening", "generated_at", "mdi:clock-check-outline"),
        ActiveProfileTextSensor(controller, "HEMS Smart Scenario Actief", "scenario", "mdi:calendar-clock"),
        ActiveProfileTextSensor(controller, "HEMS Smart Control Mode Actief", "control_mode", "mdi:transmission-tower-export"),
        ActiveProfileMetricSensor(controller, "HEMS Smart Geplande Importlimiet", "peak_shaving_limit_w", UnitOfPower.WATT, "mdi:gauge", SensorDeviceClass.POWER),
        ActiveProfileMetricSensor(controller, "HEMS Smart Gepland Target SoC", "grid_charge_target_soc", PERCENTAGE, "mdi:battery-charging-80", SensorDeviceClass.BATTERY),
        ActiveProfileMetricSensor(controller, "HEMS Smart Gepland Max Netlaadvermogen", "grid_charge_max_power_w", UnitOfPower.WATT, "mdi:ev-station", SensorDeviceClass.POWER),
        ActiveProfileMetricSensor(controller, "HEMS Smart Minimum Ontlaad SoC", "min_discharge_soc", PERCENTAGE, "mdi:battery-lock", SensorDeviceClass.BATTERY),
    ])


class _CtrlNextSensorBase:
    def _device_info(self):
        return {
            "identifiers": {(DOMAIN, self._controller.config.get('p1_sensor'))},
            "name": "CTRL-NEXT HEMS Systeem",
            "manufacturer": "CTRL-NEXT",
            "model": "HEMS AI Controller",
        }


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


class AverageBatterySocSensor(_CtrlNextSensorBase, SensorEntity):
    def __init__(self, controller):
        self._controller = controller
        self._attr_name = "HEMS Gemiddelde Batterij SoC"
        self._attr_unique_id = f"{controller.config.get('p1_sensor')}_average_battery_soc"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:battery-heart"

    @property
    def device_info(self):
        return self._device_info()

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_dispatcher_connect(self.hass, _CTRL_NEXT_UPDATE, self.async_write_ha_state)
        )

    @property
    def native_value(self):
        return round(self._controller._get_average_soc(), 1)


class BatteryTotalCapacitySensor(_CtrlNextSensorBase, SensorEntity):
    def __init__(self, controller):
        self._controller = controller
        self._attr_name = "HEMS Batterij Totaal Nominaal"
        self._attr_unique_id = f"{controller.config.get('p1_sensor')}_battery_total_nominal_kwh"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:battery"

    @property
    def device_info(self):
        return self._device_info()

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_dispatcher_connect(self.hass, _SMART_PLAN_UPDATE, self.async_write_ha_state)
        )

    @property
    def native_value(self):
        return round(self._controller._get_total_capacity_kwh(), 2)


class BatteryUsableAboveReserveSensor(_CtrlNextSensorBase, SensorEntity):
    def __init__(self, controller):
        self._controller = controller
        self._attr_name = "HEMS Batterij Bruikbaar Boven Reserve"
        self._attr_unique_id = f"{controller.config.get('p1_sensor')}_battery_usable_above_reserve_kwh"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:battery-check"

    @property
    def device_info(self):
        return self._device_info()

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_dispatcher_connect(self.hass, _SMART_PLAN_UPDATE, self.async_write_ha_state)
        )

    @property
    def native_value(self):
        total = self._controller._get_total_capacity_kwh()
        reserve_pct = max(self._controller.planner_min_reserve_soc, 0.0)
        return round(total * max(100.0 - reserve_pct, 0.0) / 100.0, 2)


class CurrentBatteryEnergySensor(_CtrlNextSensorBase, SensorEntity):
    def __init__(self, controller):
        self._controller = controller
        self._attr_name = "HEMS Batterij Energie Huidig"
        self._attr_unique_id = f"{controller.config.get('p1_sensor')}_battery_current_energy_kwh"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:battery-medium"

    @property
    def device_info(self):
        return self._device_info()

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_dispatcher_connect(self.hass, _CTRL_NEXT_UPDATE, self.async_write_ha_state)
        )

    @property
    def native_value(self):
        return round(self._controller._get_total_capacity_kwh() * self._controller._get_average_soc() / 100.0, 2)


class LiveImportHeadroomSensor(_CtrlNextSensorBase, SensorEntity):
    def __init__(self, controller):
        self._controller = controller
        self._attr_name = "HEMS Actuele Import Headroom"
        self._attr_unique_id = f"{controller.config.get('p1_sensor')}_live_import_headroom_w"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:transmission-tower"

    @property
    def device_info(self):
        return self._device_info()

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_dispatcher_connect(self.hass, _CTRL_NEXT_UPDATE, self.async_write_ha_state)
        )

    @property
    def native_value(self):
        return round(max(self._controller.planner_import_limit_w - max(self._controller.huisverbruik_value, 0.0), 0.0), 0)


class PlanSummarySensor(_CtrlNextSensorBase, SensorEntity):
    def __init__(self, controller):
        self._controller = controller
        self._attr_name = "HEMS Plan Summary"
        self._attr_unique_id = f"{controller.config.get('p1_sensor')}_smart_plan_summary"
        self._attr_icon = "mdi:clipboard-text-clock"

    @property
    def device_info(self):
        return self._device_info()

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_dispatcher_connect(self.hass, _SMART_PLAN_UPDATE, self.async_write_ha_state)
        )

    @property
    def native_value(self):
        return self._controller.smart_plan.get("summary")

    @property
    def extra_state_attributes(self):
        plan = self._controller.smart_plan
        return {
            "target_soc_morning": plan.get("target_soc_morning"),
            "target_soc_evening": plan.get("target_soc_evening"),
            "target_soc_after_super_dal": plan.get("target_soc_after_super_dal"),
            "grid_charge_needed_kwh": plan.get("grid_charge_needed_kwh"),
            "planned_grid_charge_power_w": plan.get("planned_grid_charge_power_w"),
            "planned_grid_charge_kwh": plan.get("planned_grid_charge_kwh"),
            "current_headroom_w": plan.get("current_headroom_w"),
            "expected_min_soc": plan.get("expected_min_soc"),
            "free_surplus_kwh": plan.get("free_surplus_kwh"),
            "morning_need_kwh": plan.get("morning_need_kwh"),
            "evening_need_kwh": plan.get("evening_need_kwh"),
            "day_charge_potential_kwh": plan.get("day_charge_potential_kwh"),
            "profile_quality": plan.get("profile_quality"),
            "forecast_quality": plan.get("forecast_quality"),
            "forecast_cached_since": plan.get("forecast_cached_since"),
            "forecast_cache_age_minutes": plan.get("forecast_cache_age_minutes"),
            "generated_at": plan.get("generated_at"),
            "timestamps": plan.get("timestamps", []),
            "expected_soc": plan.get("expected_soc", []),
            "expected_load_w": plan.get("expected_load_w", []),
            "expected_solar_w": plan.get("expected_solar_w", []),
            "expected_import_w": plan.get("expected_import_w", []),
            "period": plan.get("mode", []),
            "reasons": plan.get("reasons", []),
            "control_mode": plan.get("control_mode", []),
            "peak_shaving_limit_w": plan.get("peak_shaving_limit_w", []),
            "grid_charge_enabled": plan.get("grid_charge_enabled", []),
            "grid_charge_target_soc": plan.get("grid_charge_target_soc", []),
            "grid_charge_max_power_w": plan.get("grid_charge_max_power_w", []),
            "min_discharge_soc": plan.get("min_discharge_soc", []),
            "scenario": plan.get("scenario", []),
        }


class PlanMetricSensor(_CtrlNextSensorBase, SensorEntity):
    def __init__(self, controller, name, key, unit, icon, device_class):
        self._controller = controller
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{controller.config.get('p1_sensor')}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def device_info(self):
        return self._device_info()

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_dispatcher_connect(self.hass, _SMART_PLAN_UPDATE, self.async_write_ha_state)
        )

    @property
    def native_value(self):
        return self._controller.smart_plan.get(self._key)


class PlanTextSensor(_CtrlNextSensorBase, SensorEntity):
    def __init__(self, controller, name, key, icon):
        self._controller = controller
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{controller.config.get('p1_sensor')}_{key}"
        self._attr_icon = icon

    @property
    def device_info(self):
        return self._device_info()

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_dispatcher_connect(self.hass, _SMART_PLAN_UPDATE, self.async_write_ha_state)
        )

    @property
    def native_value(self):
        return self._controller.smart_plan.get(self._key)


class ActiveProfileTextSensor(_CtrlNextSensorBase, SensorEntity):
    def __init__(self, controller, name, key, icon):
        self._controller = controller
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{controller.config.get('p1_sensor')}_active_{key}"
        self._attr_icon = icon

    @property
    def device_info(self):
        return self._device_info()

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_dispatcher_connect(self.hass, _SMART_PLAN_UPDATE, self.async_write_ha_state)
        )

    @property
    def native_value(self):
        return self._controller.smart_active_profile.get(self._key)

    @property
    def extra_state_attributes(self):
        return {
            "timestamp": self._controller.smart_active_profile.get("timestamp"),
            "period": self._controller.smart_active_profile.get("period"),
            "grid_charge_enabled": self._controller.smart_active_profile.get("grid_charge_enabled"),
        }


class ActiveProfileMetricSensor(_CtrlNextSensorBase, SensorEntity):
    def __init__(self, controller, name, key, unit, icon, device_class):
        self._controller = controller
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{controller.config.get('p1_sensor')}_active_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def device_info(self):
        return self._device_info()

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_dispatcher_connect(self.hass, _SMART_PLAN_UPDATE, self.async_write_ha_state)
        )

    @property
    def native_value(self):
        return self._controller.smart_active_profile.get(self._key)

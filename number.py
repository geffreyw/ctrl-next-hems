from homeassistant.components.number import RestoreNumber
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN

_SMART_PLAN_UPDATE = "ctrl_next_plan_update"


async def async_setup_entry(hass, entry, async_add_entities):
    controller = hass.data[DOMAIN][entry.entry_id]
    specs = [
        {
            "name": "Netlaad Doel SoC (%)",
            "param": "grid_charge_target_soc",
            "min": 0,
            "max": 100,
            "step": 1,
            "icon": "mdi:battery-charging-80",
            "unit": "%",
        },
        {
            "name": "Max Netlaad Vermogen (W)",
            "param": "grid_charge_max_power_w",
            "min": 0,
            "max": 3000,
            "step": 50,
            "icon": "mdi:ev-station",
            "unit": "W",
        },
        {
            "name": "Peak Shaving Limiet (W)",
            "param": "peak_shaving_limit_w",
            "min": 500,
            "max": 10000,
            "step": 50,
            "icon": "mdi:chart-line",
            "unit": "W",
        },
        {
            "name": "Deadband (W)",
            "param": "deadband",
            "min": 0,
            "max": 200,
            "step": 1,
            "icon": "mdi:tune-vertical",
            "unit": "W",
        },
        {
            "name": "Modbus Cache Drempel (W)",
            "param": "cache_threshold",
            "min": 0,
            "max": 500,
            "step": 1,
            "icon": "mdi:memory",
            "unit": "W",
        },
        {
            "name": "Filter Alpha",
            "param": "filter_alpha",
            "min": 0.05,
            "max": 1.0,
            "step": 0.01,
            "icon": "mdi:filter-variant",
            "unit": None,
        },
        {
            "name": "Deadband Release Margin (W)",
            "param": "deadband_release_margin",
            "min": 0,
            "max": 300,
            "step": 1,
            "icon": "mdi:arrow-expand-horizontal",
            "unit": "W",
        },
        {
            "name": "Min Vermogen Per Batterij (W)",
            "param": "min_power_per_bat",
            "min": 0,
            "max": 800,
            "step": 10,
            "icon": "mdi:battery-arrow-up",
            "unit": "W",
        },
        {
            "name": "Max Vermogen Stap Per Cyclus (W)",
            "param": "max_power_step_per_cycle",
            "min": 50,
            "max": 1000,
            "step": 10,
            "icon": "mdi:stairs",
            "unit": "W",
        },
        {
            "name": "Minimale Mode Hold Tijd (s)",
            "param": "min_mode_hold_seconds",
            "min": 0,
            "max": 20,
            "step": 0.5,
            "icon": "mdi:timer-sand",
            "unit": "s",
        },
        {
            "name": "Planner Batterijcapaciteit Per Batterij (kWh)",
            "param": "planner_battery_nominal_kwh_each",
            "min": 1,
            "max": 30,
            "step": 0.01,
            "icon": "mdi:battery",
            "unit": "kWh",
        },
        {
            "name": "Planner Aantal Batterijen",
            "param": "planner_battery_count",
            "min": 1,
            "max": 8,
            "step": 1,
            "icon": "mdi:battery-sync",
            "unit": None,
        },
        {
            "name": "Planner Minimale Reserve SoC (%)",
            "param": "planner_min_reserve_soc",
            "min": 0,
            "max": 60,
            "step": 1,
            "icon": "mdi:battery-lock",
            "unit": "%",
        },
        {
            "name": "Planner Veiligheidsmarge (%)",
            "param": "planner_safety_margin_pct",
            "min": 0,
            "max": 50,
            "step": 1,
            "icon": "mdi:shield-half-full",
            "unit": "%",
        },
        {
            "name": "Planner Import Limiet (W)",
            "param": "planner_import_limit_w",
            "min": 500,
            "max": 10000,
            "step": 50,
            "icon": "mdi:transmission-tower",
            "unit": "W",
        },
    ]

    async_add_entities([
        HemsParamSlider(
            controller,
            spec["name"],
            spec["min"],
            spec["max"],
            spec["param"],
            spec["icon"],
            spec["step"],
            spec["unit"],
        )
        for spec in specs
    ])


class HemsParamSlider(RestoreNumber):
    def __init__(self, controller, name, min_val, max_val, param_name, icon, step, unit):
        self._controller = controller
        self._param_name = param_name
        self._attr_name = f"HEMS {name}"
        self._attr_native_min_value = min_val
        self._attr_native_max_value = max_val
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit
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
            self._controller.remember_manual_control_settings_if_allowed()
            if self._param_name.startswith("planner_") or self._param_name == "grid_charge_max_power_w":
                self._controller.invalidate_smart_plan()

    @property
    def native_value(self):
        return getattr(self._controller, self._param_name)

    async def async_set_native_value(self, value):
        val = float(value)
        setattr(self._controller, self._param_name, val)
        self._attr_native_value = val
        self._controller.remember_manual_control_settings_if_allowed()
        if self._param_name.startswith("planner_") or self._param_name == "grid_charge_max_power_w":
            self._controller.invalidate_smart_plan()
            async_dispatcher_send(self.hass, _SMART_PLAN_UPDATE)
        self.async_write_ha_state()

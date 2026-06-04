import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import *


def _current_value(current, key, default):
    value = current.get(key)
    return default if value in (None, "") else value


def _entity_field(current, key, default, domain):
    return (
        vol.Optional(key, default=_current_value(current, key, default)),
        selector.EntitySelector(selector.EntitySelectorConfig(domain=domain)),
    )


def _number_field(current, key, default, minimum, maximum, step, unit=None):
    return (
        vol.Optional(key, default=_current_value(current, key, default)),
        selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=minimum,
                max=maximum,
                step=step,
                mode=selector.NumberSelectorMode.BOX,
                unit_of_measurement=unit,
            )
        ),
    )


def _text_field(current, key, default):
    return (
        vol.Optional(key, default=_current_value(current, key, default)),
        selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)),
    )


def _base_schema(current=None):
    current = current or {}
    fields = {}

    fields[vol.Optional(CONF_OPERATING_MODE, default=_current_value(current, CONF_OPERATING_MODE, OPERATING_MODE_MANUAL))] = selector.SelectSelector(
        selector.SelectSelectorConfig(options=OPERATING_MODES)
    )
    fields.update(dict([
        _entity_field(current, CONF_P1_SENSOR, DEFAULT_P1_SENSOR, "sensor"),
        _text_field(current, CONF_P1_IP_ADDRESS, DEFAULT_P1_IP_ADDRESS),
        _entity_field(current, CONF_BATTERY_1_SOC, DEFAULT_BATTERY_1_SOC, "sensor"),
        _entity_field(current, CONF_BAT1_AC_POWER, DEFAULT_BAT1_AC_POWER, "sensor"),
        _entity_field(current, CONF_BAT1_CHARGE, DEFAULT_BAT1_CHARGE, "number"),
        _entity_field(current, CONF_BAT1_DISCHARGE, DEFAULT_BAT1_DISCHARGE, "number"),
        _entity_field(current, CONF_BAT1_FORCE_MODE, DEFAULT_BAT1_FORCE_MODE, "select"),
        _entity_field(current, CONF_BAT1_MODBUS_SWITCH, DEFAULT_BAT1_MODBUS_SWITCH, "switch"),
        _entity_field(current, CONF_BAT1_WORK_MODE, DEFAULT_BAT1_WORK_MODE, "select"),
        _entity_field(current, CONF_BATTERY_2_SOC, DEFAULT_BATTERY_2_SOC, "sensor"),
        _entity_field(current, CONF_BAT2_AC_POWER, DEFAULT_BAT2_AC_POWER, "sensor"),
        _entity_field(current, CONF_BAT2_CHARGE, DEFAULT_BAT2_CHARGE, "number"),
        _entity_field(current, CONF_BAT2_DISCHARGE, DEFAULT_BAT2_DISCHARGE, "number"),
        _entity_field(current, CONF_BAT2_FORCE_MODE, DEFAULT_BAT2_FORCE_MODE, "select"),
        _entity_field(current, CONF_BAT2_MODBUS_SWITCH, DEFAULT_BAT2_MODBUS_SWITCH, "switch"),
        _entity_field(current, CONF_BAT2_WORK_MODE, DEFAULT_BAT2_WORK_MODE, "select"),
    ]))

    fields.update(dict([
        _entity_field(current, CONF_FORECAST_SOLAR_TODAY, DEFAULT_FORECAST_SOLAR_TODAY, "sensor"),
        _entity_field(current, CONF_FORECAST_SOLAR_REMAINING_TODAY, DEFAULT_FORECAST_SOLAR_REMAINING_TODAY, "sensor"),
        _entity_field(current, CONF_FORECAST_SOLAR_TOMORROW, DEFAULT_FORECAST_SOLAR_TOMORROW, "sensor"),
        _entity_field(current, CONF_FORECAST_SOLAR_THIS_HOUR, DEFAULT_FORECAST_SOLAR_THIS_HOUR, "sensor"),
        _entity_field(current, CONF_FORECAST_SOLAR_NEXT_HOUR, DEFAULT_FORECAST_SOLAR_NEXT_HOUR, "sensor"),
        _entity_field(current, CONF_FORECAST_SOLAR_POWER_NOW, DEFAULT_FORECAST_SOLAR_POWER_NOW, "sensor"),
        _entity_field(current, CONF_FORECAST_SOLAR_POWER_IN_24H, DEFAULT_FORECAST_SOLAR_POWER_IN_24H, "sensor"),
        _entity_field(current, CONF_FORECAST_SOLAR_PEAK_TODAY, DEFAULT_FORECAST_SOLAR_PEAK_TODAY, "sensor"),
        _entity_field(current, CONF_FORECAST_SOLAR_PEAK_TOMORROW, DEFAULT_FORECAST_SOLAR_PEAK_TOMORROW, "sensor"),
    ]))

    fields.update(dict([
        _text_field(current, CONF_PLANNER_NOTIFY_SERVICE, DEFAULT_PLANNER_NOTIFY_SERVICE),
        _text_field(current, CONF_PLANNER_DASHBOARD_PATH, DEFAULT_PLANNER_DASHBOARD_PATH),
        _number_field(current, CONF_PLANNER_BATTERY_NOMINAL_KWH_EACH, DEFAULT_PLANNER_BATTERY_NOMINAL_KWH_EACH, 1, 30, 0.01, "kWh"),
        _number_field(current, CONF_PLANNER_BATTERY_COUNT, DEFAULT_PLANNER_BATTERY_COUNT, 1, 8, 1),
        _number_field(current, CONF_PLANNER_MIN_RESERVE_SOC, DEFAULT_PLANNER_MIN_RESERVE_SOC, 0, 60, 1, "%"),
        _number_field(current, CONF_PLANNER_SAFETY_MARGIN_PCT, DEFAULT_PLANNER_SAFETY_MARGIN_PCT, 0, 50, 1, "%"),
        _number_field(current, CONF_PLANNER_IMPORT_LIMIT_W, DEFAULT_PLANNER_IMPORT_LIMIT_W, 500, 10000, 50, "W"),
    ]))

    return vol.Schema(fields)


class CtrlNextConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        return CtrlNextOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="CTRL-NEXT HEMS", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_base_schema(),
            errors=errors,
        )


class CtrlNextOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self._config_entry.data, **self._config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_base_schema(current),
        )

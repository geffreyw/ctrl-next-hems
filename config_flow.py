import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import *


class CtrlNextConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        return CtrlNextOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="CTRL-NEXT HEMS", data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_P1_SENSOR): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Optional(CONF_P1_HTTP_URL, default=""): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.URL)
            ),
            vol.Optional(CONF_P1_HTTP_JSON_KEY, default="power"): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
            ),
            vol.Optional(CONF_P1_HTTP_TIMEOUT, default=2.0): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.5,
                    max=10,
                    step=0.5,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="s",
                )
            ),
            # Batterij 1
            vol.Required(CONF_BATTERY_1_SOC): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Required(CONF_BAT1_AC_POWER): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Required(CONF_BAT1_CHARGE): selector.EntitySelector(selector.EntitySelectorConfig(domain="number")),
            vol.Required(CONF_BAT1_DISCHARGE): selector.EntitySelector(selector.EntitySelectorConfig(domain="number")),
            vol.Required(CONF_BAT1_FORCE_MODE): selector.EntitySelector(selector.EntitySelectorConfig(domain="select")),
            vol.Required(CONF_BAT1_MODBUS_SWITCH): selector.EntitySelector(selector.EntitySelectorConfig(domain="switch")),
            vol.Required(CONF_BAT1_WORK_MODE): selector.EntitySelector(selector.EntitySelectorConfig(domain="select")),
            # Batterij 2
            vol.Required(CONF_BATTERY_2_SOC): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Required(CONF_BAT2_AC_POWER): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Required(CONF_BAT2_CHARGE): selector.EntitySelector(selector.EntitySelectorConfig(domain="number")),
            vol.Required(CONF_BAT2_DISCHARGE): selector.EntitySelector(selector.EntitySelectorConfig(domain="number")),
            vol.Required(CONF_BAT2_FORCE_MODE): selector.EntitySelector(selector.EntitySelectorConfig(domain="select")),
            vol.Required(CONF_BAT2_MODBUS_SWITCH): selector.EntitySelector(selector.EntitySelectorConfig(domain="switch")),
            vol.Required(CONF_BAT2_WORK_MODE): selector.EntitySelector(selector.EntitySelectorConfig(domain="select")),
        })
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)


class CtrlNextOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self._config_entry.data, **self._config_entry.options}

        data_schema = vol.Schema({
            vol.Optional(CONF_P1_HTTP_URL, default=current.get(CONF_P1_HTTP_URL, "")): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.URL)
            ),
            vol.Optional(CONF_P1_HTTP_JSON_KEY, default=current.get(CONF_P1_HTTP_JSON_KEY, "power")): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
            ),
            vol.Optional(CONF_P1_HTTP_TIMEOUT, default=float(current.get(CONF_P1_HTTP_TIMEOUT, 2.0))): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.5,
                    max=10,
                    step=0.5,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="s",
                )
            ),
        })

        return self.async_show_form(step_id="init", data_schema=data_schema)
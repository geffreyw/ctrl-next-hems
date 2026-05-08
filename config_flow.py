import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import *

class CtrlNextConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="CTRL-NEXT HEMS", data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_P1_SENSOR): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
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
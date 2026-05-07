import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import DOMAIN, CONF_P1_SENSOR, CONF_BATTERY_1_SOC, CONF_BATTERY_2_SOC

class MarstekManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """De UI configuratie voor Marstek Manager."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Behandel de eerste stap van de configuratie in de HA interface."""
        errors = {}

        if user_input is not None:
            # Hier controleren we later of de sensoren echt bestaan, voor nu keuren we het goed
            return self.async_create_entry(title="Marstek HEMS Manager", data=user_input)

        # Het formulier dat we in Home Assistant tonen
        data_schema = vol.Schema({
            vol.Required(CONF_P1_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_BATTERY_1_SOC): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_BATTERY_2_SOC): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

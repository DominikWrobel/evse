import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

class EVSEFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Try connecting to the provided IP and port
            return self.async_create_entry(title=user_input['name'], data=user_input)
        
        data_schema = vol.Schema({
            vol.Required('ip_address'): str,
            vol.Required('port', default=80): int,
            vol.Required('name'): str
        })
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return EVSEOptionsFlowHandler(config_entry)

class EVSEOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        
        data_schema = vol.Schema({
            vol.Optional('ip_address', default=self.config_entry.data.get('ip_address')): str,
            vol.Optional('port', default=self.config_entry.data.get('port')): int,
            vol.Optional('name', default=self.config_entry.data.get('name')): str
        })
        return self.async_show_form(step_id="init", data_schema=data_schema)

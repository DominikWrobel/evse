from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import asyncio
import logging

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the EVSE switch."""
    ip = config_entry.data['ip_address']
    port = config_entry.data['port']
    name = config_entry.data['name']

    switch = EVSESwitch(hass, f"{name}_switch", ip, port)
    async_add_entities([switch], True)

class EVSESwitch(SwitchEntity):
    """Representation of an EVSE switch."""

    def __init__(self, hass, name, ip, port):
        """Initialize the switch."""
        self.hass = hass
        self._name = name
        self._ip = ip
        self._port = port
        self._state = None
        self._available = True
        self._unique_id = f"{self._name}_switch"
        self._attr_extra_state_attributes = {}

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID of the switch."""
        return self._unique_id

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._state

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self._send_command("setStatus?active=true")
        self._state = True

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._send_command("setStatus?active=false")
        self._state = False

    async def _send_command(self, command):
        """Send command to EVSE."""
        url = f"http://{self._ip}:{self._port}/{command}"
        try:
            session = async_get_clientsession(self.hass)
            async with asyncio.timeout(10):
                async with session.get(url) as response:
                    await response.text()
            self._available = True
        except asyncio.TimeoutError:
            self._available = False
            _LOGGER.error("Timeout error sending command to %s", url)
        except Exception as e:
            self._available = False
            _LOGGER.error("Error sending command to %s: %s", url, str(e))

    async def async_update(self):
        """Fetch new state data for the switch."""
        url = f"http://{self._ip}:{self._port}/getParameters"
        try:
            session = async_get_clientsession(self.hass)
            async with asyncio.timeout(10):
                async with session.get(url) as response:
                    data = await response.json()
                    evse_state = data["list"][0].get("evseState")
                    self._state = evse_state == "true" or evse_state is True
            self._available = True
        except asyncio.TimeoutError:
            self._state = None
            self._available = False
            _LOGGER.error("Timeout error fetching data from %s", url)
        except Exception as e:
            self._state = None
            self._available = False
            _LOGGER.error("Error fetching data from %s: %s", url, str(e))

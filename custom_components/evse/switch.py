from homeassistant.components.switch import SwitchEntity
import aiohttp
import async_timeout

from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the EVSE switch."""
    ip = config_entry.data['ip_address']
    port = config_entry.data['port']
    name = config_entry.data['name']

    switch = EVSESwitch(f"{name}_switch", ip, port)
    async_add_entities([switch], True)

class EVSESwitch(SwitchEntity):
    """Representation of an EVSE switch."""

    def __init__(self, name, ip, port):
        """Initialize the switch."""
        self._name = name
        self._ip = ip
        self._port = port
        self._state = None
        self._available = True
        self._unique_id = f"{self._name}_switch"

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
        await self._send_command("activate")
        self._state = True

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._send_command("deactivate")
        self._state = False

    async def _send_command(self, command):
        """Send command to EVSE."""
        url = f"http://{self._ip}:{self._port}/{command}"
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(10):
                    async with session.get(url) as response:
                        await response.text()
            self._available = True
        except Exception as e:
            self._available = False
            self.hass.components.logger.error(f"Error sending command to {url}: {e}")

    async def async_update(self):
        """Fetch new state data for the switch."""
        url = f"http://{self._ip}:{self._port}/getParameters"
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(10):
                    async with session.get(url) as response:
                        data = await response.json()
                        evse_state = data["list"][0].get("evseState")
                        self._state = evse_state == "true"
            self._available = True
        except Exception as e:
            self._state = None
            self._available = False
            self.hass.components.logger.error(f"Error fetching data from {url}: {e}")
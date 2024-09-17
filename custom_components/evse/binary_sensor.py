from homeassistant.components.binary_sensor import BinarySensorEntity
import aiohttp
import async_timeout

from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the EVSE binary sensors."""
    ip = config_entry.data['ip_address']
    port = config_entry.data['port']
    name = config_entry.data['name']

    sensors = [
        EVSEBinarySensor(f"{name}_evse_state", ip, port, "evseState", "EVSE State")
    ]

    async_add_entities(sensors, True)

class EVSEBinarySensor(BinarySensorEntity):
    """Representation of an EVSE binary sensor."""

    def __init__(self, name, ip, port, attribute, friendly_name):
        """Initialize the binary sensor."""
        self._name = name
        self._ip = ip
        self._port = port
        self._attribute = attribute
        self._friendly_name = friendly_name
        self._state = None
        self._unique_id = f"{self._name}_{self._attribute}"  # Unique ID

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def is_on(self):
        """Return true if the sensor is on."""
        return self._state == "1"

    async def async_update(self):
        """Fetch new state data for the sensor."""
        url = f"http://{self._ip}:{self._port}/getParameters"
        try:
            async with aiohttp.ClientSession() as session:
                with async_timeout.timeout(10):
                    async with session.get(url) as response:
                        data = await response.json()
                        self._state = data["list"][0].get(self._attribute)
        except Exception as e:
            self._state = None
            # Log the error in the Home Assistant log
            self.hass.components.logger.error(f"Error fetching data from {url}: {e}")


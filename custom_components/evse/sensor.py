import aiohttp
import asyncio
import async_timeout
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.exceptions import ConfigEntryNotReady
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class EVSESensor(SensorEntity):
    """Representation of an EVSE sensor."""

    def __init__(self, name, ip, port, attribute, unit, friendly_name):
        """Initialize the sensor."""
        self._name = name
        self._ip = ip
        self._port = port
        self._attribute = attribute
        self._unit = unit
        self._friendly_name = friendly_name
        self._state = None
        self._attr_unique_id = f"{self._name}_{self._attribute}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._attribute == "vehicleState":
            return self._map_vehicle_state(self._state)
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    def _map_vehicle_state(self, value):
        """Map vehicle state codes to human-readable values."""
        mapper = {
            1: "Ready",
            2: "Connected",
            3: "Charging",
            5: "Error"
        }
        return mapper.get(value, "Unknown")

    async def async_update(self):
        """Fetch new state data for the sensor."""
        url = f"http://{self._ip}:{self._port}/getParameters"
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(10):
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            self._state = data["list"][0].get(self._attribute)
                        else:
                            _LOGGER.error(f"Error fetching data from {url}: HTTP status {response.status}")
                            self._state = None
        except aiohttp.ClientConnectorError as e:
            _LOGGER.error(f"Connection error for {url}: {e}")
            self._state = None
        except asyncio.TimeoutError:
            _LOGGER.error(f"Timeout error for {url}")
            self._state = None
        except Exception as e:
            _LOGGER.error(f"Unexpected error fetching data from {url}: {e}")
            self._state = None

class EVSECurrentSlider(NumberEntity):
    """Representation of an EVSE current slider."""

    def __init__(self, name, ip, port):
        """Initialize the current slider."""
        self._name = name
        self._ip = ip
        self._port = port
        self._value = None
        self._attr_unique_id = f"{self._name}_slider"

    @property
    def name(self):
        """Return the name of the slider."""
        return self._name

    @property
    def native_value(self):
        """Return the current value of the slider."""
        return self._value

    @property
    def native_min_value(self):
        """Return the minimum value of the slider."""
        return 0

    @property
    def native_max_value(self):
        """Return the maximum value of the slider."""
        return 16

    @property
    def native_step(self):
        """Return the step value of the slider."""
        return 1

    async def async_set_native_value(self, value):
        """Set the current value of the slider."""
        url = f"http://{self._ip}:{self._port}/setCurrent?current={value}"
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(10):
                    async with session.get(url) as response:
                        if response.status == 200:
                            await response.text()
                            self._value = value
                        else:
                            _LOGGER.error(f"Error setting current: HTTP status {response.status}")
        except aiohttp.ClientConnectorError as e:
            _LOGGER.error(f"Connection error setting current: {e}")
        except asyncio.TimeoutError:
            _LOGGER.error(f"Timeout error setting current")
        except Exception as e:
            _LOGGER.error(f"Unexpected error setting current: {e}")

    async def async_update(self):
        """Fetch new state data for the slider."""
        url = f"http://{self._ip}:{self._port}/getParameters"
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(10):
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            self._value = data["list"][0].get("maxCurrent")
                        else:
                            _LOGGER.error(f"Error fetching data from {url}: HTTP status {response.status}")
                            self._value = None
        except aiohttp.ClientConnectorError as e:
            _LOGGER.error(f"Connection error for {url}: {e}")
            self._value = None
        except asyncio.TimeoutError:
            _LOGGER.error(f"Timeout error for {url}")
            self._value = None
        except Exception as e:
            _LOGGER.error(f"Unexpected error fetching data from {url}: {e}")
            self._value = None

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the EVSE sensors and number entities from a config entry."""
    ip = config_entry.data['ip_address']
    port = config_entry.data['port']
    name = config_entry.data['name']

    # Test connection before setting up entities
    try:
        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(10):
                async with session.get(f"http://{ip}:{port}/getParameters") as response:
                    if response.status != 200:
                        raise ConfigEntryNotReady(f"EVSE device returned status {response.status}")
    except aiohttp.ClientConnectorError as e:
        raise ConfigEntryNotReady(f"Failed to connect to EVSE device: {e}")
    except asyncio.TimeoutError:
        raise ConfigEntryNotReady("Connection to EVSE device timed out")

    # Create sensor entities
    sensors = [
        EVSESensor(f"{name}_actual_current", ip, port, "actualCurrent", "A", "Actual Current"),
        EVSESensor(f"{name}_actual_power", ip, port, "actualPower", "kW", "Actual Power"),
        EVSESensor(f"{name}_duration", ip, port, "duration", "Minutes", "Duration"),
        EVSESensor(f"{name}_vehicle_state", ip, port, "vehicleState", None, "Vehicle State"),
        EVSESensor(f"{name}_max_current", ip, port, "maxCurrent", "A", "Max Current"),
        EVSESensor(f"{name}_actual_current_ma", ip, port, "actualCurrentMA", "mA", "Actual Current (mA)"),
        EVSESensor(f"{name}_always_active", ip, port, "alwaysActive", None, "Always Active"),
        EVSESensor(f"{name}_last_action_user", ip, port, "lastActionUser", None, "Last Action User"),
        EVSESensor(f"{name}_last_action_uid", ip, port, "lastActionUID", None, "Last Action UID"),
        EVSESensor(f"{name}_energy", ip, port, "energy", "kWh", "Energy"),  # Corrected friendly_name
        EVSESensor(f"{name}_mileage", ip, port, "mileage", "km", "Mileage"),
        EVSESensor(f"{name}_meter_reading", ip, port, "meterReading", "kWh", "Meter Reading"),
        EVSESensor(f"{name}_current_p1", ip, port, "currentP1", "A", "Current Phase 1"),
        EVSESensor(f"{name}_current_p2", ip, port, "currentP2", "A", "Current Phase 2"),
        EVSESensor(f"{name}_current_p3", ip, port, "currentP3", "A", "Current Phase 3"),
        EVSESensor(f"{name}_voltage_p1", ip, port, "voltageP1", "V", "Voltage Phase 1"),
        EVSESensor(f"{name}_voltage_p2", ip, port, "voltageP2", "V", "Voltage Phase 2"),
        EVSESensor(f"{name}_voltage_p3", ip, port, "voltageP3", "V", "Voltage Phase 3"),
        EVSESensor(f"{name}_use_meter", ip, port, "useMeter", None, "Use Meter"),
        EVSESensor(f"{name}_rfid_uid", ip, port, "RFIDUID", None, "RFID UID")
    ]

    # Add the current slider
    current_slider = EVSECurrentSlider(f"{name}_set_current", ip, port)

    # Add the sensors and slider
    async_add_entities(sensors + [current_slider], True)


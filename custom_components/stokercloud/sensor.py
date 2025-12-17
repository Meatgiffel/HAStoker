from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfMass,
    UnitOfPower,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _find_id(
    items: list[dict[str, Any]] | None, wanted_id: str
) -> dict[str, Any] | None:
    if not items:
        return None
    for item in items:
        if str(item.get("id")) == wanted_id:
            return item
    return None


def _get_list_value(
    data: dict[str, Any], section: str, wanted_id: str
) -> Any | None:
    item = _find_id(data.get(section), wanted_id)
    if not item:
        return None
    return item.get("value")


def _get_front_value(data: dict[str, Any], front_id: str) -> Any | None:
    item = _find_id(data.get("frontdata"), front_id)
    if not item:
        return None
    return item.get("value")


def _get_left_output_value(data: dict[str, Any], output_id: str) -> Any | None:
    leftoutput = data.get("leftoutput", {})
    if not isinstance(leftoutput, dict):
        return None
    output = leftoutput.get(output_id, {})
    if not isinstance(output, dict):
        return None
    return output.get("val")


def _as_float(value: Any) -> float | None:
    if value in (None, "", "N/A"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True, slots=True)
class StokerCloudSensorSpec:
    description: SensorEntityDescription
    value_fn: Callable[[dict[str, Any]], Any | None]


SENSORS: tuple[StokerCloudSensorSpec, ...] = (
    # Weather (top-left panel)
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="weather_city",
            name="Weather city",
            icon="mdi:city",
        ),
        lambda data: _get_list_value(data, "weatherdata", "weather-city"),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="outdoor_temperature",
            name="Outdoor temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_list_value(data, "weatherdata", "1")),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="wind_speed",
            name="Wind speed",
            device_class=SensorDeviceClass.WIND_SPEED,
            native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_list_value(data, "weatherdata", "2")),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="wind_direction",
            name="Wind direction",
            icon="mdi:compass",
        ),
        lambda data: _get_list_value(data, "weatherdata", "3"),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="clouds",
            name="Clouds",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_list_value(data, "weatherdata", "9")),
    ),
    # Boiler (bottom-left panel)
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="chimney_smoke_temperature",
            name="Chimney/smoke temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_list_value(data, "boilerdata", "3")),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="power_output",
            name="Power output",
            device_class=SensorDeviceClass.POWER,
            native_unit_of_measurement=UnitOfPower.KILO_WATT,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_list_value(data, "boilerdata", "5")),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="power_percentage",
            name="Power (%)",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_list_value(data, "boilerdata", "4")),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="photo_sensor_light",
            name="Photo sensor (light)",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_list_value(data, "boilerdata", "6")),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="oxygen",
            name="Oxygen (%)",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_list_value(data, "boilerdata", "12")),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="oxygen_reference",
            name="Oxygen reference",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_front_value(data, "refoxygen")),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="o2_low_regulation",
            name="O2 low regulation (%)",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_list_value(data, "boilerdata", "14")),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="o2_mid_regulation",
            name="O2 mid regulation (%)",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_list_value(data, "boilerdata", "15")),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="o2_high_regulation",
            name="O2 high regulation (%)",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_list_value(data, "boilerdata", "16")),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="online_time",
            name="Online time",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_list_value(data, "boilerdata", "9")),
    ),
    # Front readout (shows boiler temp and setpoint)
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="boiler_temperature",
            name="Boiler temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_front_value(data, "boilertemp")),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="wanted_boiler_temperature",
            name="Wanted boiler temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_front_value(data, "-wantedboilertemp")),
    ),
    # Icons on the left side
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="pump_output",
            name="Pump output",
            icon="mdi:pump",
        ),
        lambda data: _get_left_output_value(data, "output-2"),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="compressor",
            name="Compressor",
            icon="mdi:air-compressor",
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_left_output_value(data, "output-7")),
    ),
    # Hopper (center-right panel)
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="hopper_content",
            name="Hopper content",
            device_class=SensorDeviceClass.WEIGHT,
            native_unit_of_measurement=UnitOfMass.KILOGRAMS,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_front_value(data, "hoppercontent")),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="auger_capacity",
            name="Auger capacity",
            device_class=SensorDeviceClass.WEIGHT,
            native_unit_of_measurement=UnitOfMass.GRAMS,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_list_value(data, "hopperdata", "2")),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="consumption_last_24h",
            name="Consumption last 24 h",
            device_class=SensorDeviceClass.WEIGHT,
            native_unit_of_measurement=UnitOfMass.KILOGRAMS,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_list_value(data, "hopperdata", "3")),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="consumption_total",
            name="Consumption total",
            device_class=SensorDeviceClass.WEIGHT,
            native_unit_of_measurement=UnitOfMass.KILOGRAMS,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        lambda data: _as_float(_get_list_value(data, "hopperdata", "4")),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="power_10pct",
            name="Power 10%",
            device_class=SensorDeviceClass.POWER,
            native_unit_of_measurement=UnitOfPower.KILO_WATT,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_list_value(data, "hopperdata", "7")),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="power_100pct",
            name="Power 100%",
            device_class=SensorDeviceClass.POWER,
            native_unit_of_measurement=UnitOfPower.KILO_WATT,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_list_value(data, "hopperdata", "8")),
    ),
    # DHW (right panel)
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="dhw_temperature",
            name="DHW temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_front_value(data, "dhw")),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="wanted_dhw_temperature",
            name="Wanted DHW temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_front_value(data, "dhwwanted")),
    ),
    StokerCloudSensorSpec(
        SensorEntityDescription(
            key="dhw_difference",
            name="DHW difference",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        lambda data: _as_float(_get_list_value(data, "dhwdata", "3")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entry_data: dict[str, Any] = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator = entry_data["coordinator"]
    event_coordinator: DataUpdateCoordinator | None = entry_data.get(
        "event_coordinator"
    )

    entities: list[SensorEntity] = [
        StokerCloudSensor(coordinator, entry, spec) for spec in SENSORS
    ]
    if event_coordinator is not None:
        entities.append(
            StokerCloudEventLogSensor(event_coordinator, coordinator, entry)
        )

    async_add_entities(entities)


class StokerCloudSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        spec: StokerCloudSensorSpec,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = spec.description
        self._spec = spec
        entry_uid = entry.unique_id or entry.entry_id
        self._attr_unique_id = f"{entry_uid}_{spec.description.key}"

    @property
    def native_value(self) -> Any | None:
        return self._spec.value_fn(self.coordinator.data)

    @property
    def device_info(self) -> dict[str, Any] | None:
        data = self.coordinator.data or {}
        serial = data.get("serial")
        alias = data.get("alias")
        if not serial and not alias:
            return None
        return {
            "identifiers": {(DOMAIN, str(serial or alias))},
            "name": f"{serial} / {alias}" if serial and alias else str(serial or alias),
            "manufacturer": "StokerCloud",
            "model": str(data.get("model") or "pellet furnace"),
        }


_MAX_STATE_ATTR_BYTES = 16_000


def _truncate_events_for_attributes(
    events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], bool]:
    if not events:
        return events, False

    def _size(candidate: list[dict[str, Any]]) -> int:
        return len(json.dumps(candidate, separators=(",", ":"), ensure_ascii=False))

    if _size(events) <= _MAX_STATE_ATTR_BYTES:
        return events, False

    low, high = 1, len(events)
    best = 1
    while low <= high:
        mid = (low + high) // 2
        if _size(events[:mid]) <= _MAX_STATE_ATTR_BYTES:
            best = mid
            low = mid + 1
        else:
            high = mid - 1

    return events[:best], True


class StokerCloudEventLogSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device_coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._device_coordinator = device_coordinator
        entry_uid = entry.unique_id or entry.entry_id
        self._attr_unique_id = f"{entry_uid}_event_log"
        self.entity_description = SensorEntityDescription(
            key="event_log",
            name="Event log",
            icon="mdi:clipboard-text-clock",
        )

    @property
    def native_value(self) -> Any | None:
        data = self.coordinator.data or {}
        events = data.get("events")
        if isinstance(events, list):
            return len(events)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        events = data.get("events")
        if not isinstance(events, list):
            return {}

        cleaned = [event for event in events if isinstance(event, dict)]
        truncated_events, truncated = _truncate_events_for_attributes(cleaned)

        attrs: dict[str, Any] = {
            "events": truncated_events,
            "events_total": len(cleaned),
            "events_truncated": truncated,
        }
        for key in ("count", "offset", "translation_language", "translations_loaded"):
            if key in data:
                attrs[key] = data[key]
        return attrs

    @property
    def device_info(self) -> dict[str, Any] | None:
        data = self._device_coordinator.data or {}
        serial = data.get("serial")
        alias = data.get("alias")
        if not serial and not alias:
            return None
        return {
            "identifiers": {(DOMAIN, str(serial or alias))},
            "name": f"{serial} / {alias}" if serial and alias else str(serial or alias),
            "manufacturer": "StokerCloud",
            "model": str(data.get("model") or "pellet furnace"),
        }

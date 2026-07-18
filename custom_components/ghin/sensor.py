"""Sensor platform for the GHIN integration."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]

    async_add_entities(
        [
            GhinHandicapSensor(coordinator, client, entry),
            GhinLowHiSensor(coordinator, client, entry),
            GhinLastScoreSensor(coordinator, client, entry),
            GhinScoringAverageSensor(coordinator, client, entry),
        ]
    )


class GhinBaseSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, client, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._client = client
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._client.ghin_number or self._entry.entry_id)},
            name=f"GHIN - {self._client.club_name or 'Golfer'}",
            manufacturer="USGA / GHIN",
            model="Handicap Index",
        )


class GhinHandicapSensor(GhinBaseSensor):
    _attr_name = "Handicap Index"
    _attr_native_unit_of_measurement = None
    _attr_icon = "mdi:golf"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_handicap_index"

    @property
    def native_value(self):
        return self.coordinator.data.get("handicap_index")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        return {
            "club_name": data.get("club_name"),
            "revision_date": data.get("rev_date"),
            "ghin_number": data.get("ghin_number"),
        }


class GhinLowHiSensor(GhinBaseSensor):
    _attr_name = "Low HI"
    _attr_icon = "mdi:trending-down"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_low_hi"

    @property
    def native_value(self):
        return self.coordinator.data.get("low_hi_display")


class GhinLastScoreSensor(GhinBaseSensor):
    _attr_name = "Last Round Score"
    _attr_icon = "mdi:scorecard"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_last_score"

    @property
    def native_value(self):
        last_score = self.coordinator.data.get("last_score")
        if not last_score:
            return None
        return last_score.get("adjusted_gross_score")

    @property
    def extra_state_attributes(self):
        last_score = self.coordinator.data.get("last_score")
        if not last_score:
            return {}
        return {
            "played_at": last_score.get("played_at"),
            "course_name": last_score.get("course_name"),
            "tee_name": last_score.get("tee_name"),
            "net_score": last_score.get("net_score"),
            "to_par": last_score.get("to_par_display_value"),
            "differential": last_score.get("differential"),
            "course_handicap": last_score.get("course_handicap"),
            "course_rating": last_score.get("course_rating"),
            "slope_rating": last_score.get("slope_rating"),
            "status": last_score.get("status"),
        }


class GhinScoringAverageSensor(GhinBaseSensor):
    _attr_name = "Scoring Average"
    _attr_icon = "mdi:chart-line"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_scoring_average"

    @property
    def native_value(self):
        return self.coordinator.data.get("average")

    @property
    def extra_state_attributes(self):
        return {
            "lowest_score": self.coordinator.data.get("lowest_score"),
            "highest_score": self.coordinator.data.get("highest_score"),
            "total_rounds_posted": self.coordinator.data.get("total_count"),
        }

"""Sensors for Dengue Watch Thailand."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DASHBOARD_URL, DOMAIN, NAME
from .coordinator import DengueConfigEntry, DengueCoordinator
from .surveillance import LEVELS, WINDOW_WEEKS, DengueStatus, week_start


def _week_label(year: int, week: int) -> str:
    return f"{year}-W{week:02d}"


def _level_attrs(d: DengueStatus, c: DengueCoordinator) -> dict[str, Any]:
    y, w = d.last_week
    return {
        "province": c.province,
        "province_th": c.province_th,
        "cases_last_4_weeks": int(d.cases_window),
        "expected_last_4_weeks": d.expected_window,
        "ratio": d.ratio,
        "trend": d.trend,
        "cases_this_year": int(d.cases_year),
        "cases_same_period_last_year": int(d.cases_year_last) if d.cases_year_last is not None else None,
        "latest_week": _week_label(y, w),
        "latest_week_start": week_start(y, w).isoformat(),
        "baseline_years": d.baseline_years,
        "weeks": [_week_label(p.year, p.week) for p in d.weeks],
        "weekly_cases": [None if p.cases is None else int(p.cases) for p in d.weeks],
        "weekly_median": [p.median for p in d.weeks],
        "window_weeks": WINDOW_WEEKS,
        "source": DASHBOARD_URL,
    }


@dataclass(frozen=True, kw_only=True)
class DengueSensorDescription(SensorEntityDescription):
    value: Callable[[DengueStatus], Any]
    attrs: Callable[[DengueStatus, DengueCoordinator], dict[str, Any]] | None = None


SENSORS: tuple[DengueSensorDescription, ...] = (
    DengueSensorDescription(
        key="level",
        translation_key="level",
        device_class=SensorDeviceClass.ENUM,
        options=LEVELS,
        icon="mdi:mosquito",
        value=lambda d: d.level,
        attrs=_level_attrs,
    ),
    DengueSensorDescription(
        key="cases_4_weeks",
        translation_key="cases_4_weeks",
        native_unit_of_measurement="cases",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:account-alert-outline",
        value=lambda d: int(d.cases_window),
    ),
    DengueSensorDescription(
        key="cases_year",
        translation_key="cases_year",
        native_unit_of_measurement="cases",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:calendar-text-outline",
        value=lambda d: int(d.cases_year),
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: DengueConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(DengueSensor(coordinator, entry, desc) for desc in SENSORS)


class DengueSensor(CoordinatorEntity[DengueCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    entity_description: DengueSensorDescription

    def __init__(self, coordinator: DengueCoordinator, entry: DengueConfigEntry, desc: DengueSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = desc
        self._attr_unique_id = f"{entry.entry_id}_{desc.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Department of Disease Control (DDC), Thailand",
            model=f"{NAME} · Report 506",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=DASHBOARD_URL,
        )

    @property
    def native_value(self) -> Any:
        return self.entity_description.value(self.coordinator.data) if self.coordinator.data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if not self.coordinator.data or not self.entity_description.attrs:
            return None
        return self.entity_description.attrs(self.coordinator.data, self.coordinator)

"""Sensors: one device per province, a level and case counts per disease."""

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

from .const import ATTRIBUTION, DASHBOARD_URL, DISEASES, DOMAIN, NAME, PROVINCES
from .coordinator import DengueConfigEntry, DengueCoordinator, Key
from .surveillance import LEVELS, WINDOW_WEEKS, DengueStatus, week_start


def _week_label(year: int, week: int) -> str:
    return f"{year}-W{week:02d}"


def _level_attrs(d: DengueStatus, c: DengueCoordinator, key: Key) -> dict[str, Any]:
    province, disease = key
    y, w = d.last_week
    return {
        "province": province,
        "province_th": PROVINCES[province],
        "disease": disease,
        "disease_name": DISEASES[disease]["name"],
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
        "fetched": c.fetched_at(key),
        "source": DASHBOARD_URL,
    }


@dataclass(frozen=True, kw_only=True)
class DengueSensorDescription(SensorEntityDescription):
    value: Callable[[DengueStatus], Any]
    suffix: str
    attrs: Callable[[DengueStatus, DengueCoordinator, Key], dict[str, Any]] | None = None


SENSORS: tuple[DengueSensorDescription, ...] = (
    DengueSensorDescription(
        key="level",
        suffix="level",
        translation_key="level",
        device_class=SensorDeviceClass.ENUM,
        options=LEVELS,
        icon="mdi:virus-outline",
        value=lambda d: d.level,
        attrs=_level_attrs,
    ),
    DengueSensorDescription(
        key="cases_4_weeks",
        suffix="cases_last_4_weeks",
        translation_key="cases_4_weeks",
        native_unit_of_measurement="cases",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:account-alert-outline",
        value=lambda d: int(d.cases_window),
    ),
    DengueSensorDescription(
        key="cases_year",
        suffix="cases_this_year",
        translation_key="cases_year",
        native_unit_of_measurement="cases",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:calendar-text-outline",
        entity_registry_enabled_default=False,
        value=lambda d: int(d.cases_year),
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: DengueConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(DengueSensor(coordinator, entry, key, desc) for key in coordinator.pairs for desc in SENSORS)


class DengueSensor(CoordinatorEntity[DengueCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    entity_description: DengueSensorDescription

    def __init__(self, coordinator: DengueCoordinator, entry: DengueConfigEntry, key: Key, desc: DengueSensorDescription) -> None:
        super().__init__(coordinator)
        province, disease = key
        self._key = key
        self.entity_description = desc
        slug = province.lower().replace(" ", "_")
        self._attr_unique_id = f"{entry.entry_id}_{slug}_{disease}_{desc.key}"
        self._attr_translation_placeholders = {"disease": DISEASES[disease]["name"]}
        # predictable ids such as sensor.dengue_krabi_level or sensor.malaria_phuket_cases_last_4_weeks
        self.entity_id = f"sensor.{disease}_{slug}_{desc.suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_{slug}")},
            name=f"Mosquito Watch {province}",
            manufacturer="Department of Disease Control (DDC), Thailand",
            model=f"{NAME} · Report 506",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=DASHBOARD_URL,
        )

    @property
    def _status(self) -> DengueStatus | None:
        return (self.coordinator.data or {}).get(self._key)

    @property
    def available(self) -> bool:
        return self._status is not None

    @property
    def native_value(self) -> Any:
        st = self._status
        return self.entity_description.value(st) if st else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        st = self._status
        if not st or not self.entity_description.attrs:
            return None
        return self.entity_description.attrs(st, self.coordinator, self._key)

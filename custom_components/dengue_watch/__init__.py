"""Dengue Watch Thailand - mosquito-borne diseases per province from the DDC surveillance (Report 506)."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import CONF_DISEASES, CONF_PROVINCE, CONF_PROVINCES, DOMAIN
from .coordinator import DengueConfigEntry, DengueCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
CARD_URL = f"/{DOMAIN}/mosquito-watch-card.js"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the Mosquito Watch card and load it in every dashboard."""
    card = Path(__file__).parent / "frontend" / "mosquito-watch-card.js"
    version = card.stat().st_mtime_ns if card.exists() else 0
    await hass.http.async_register_static_paths([StaticPathConfig(CARD_URL, str(card), True)])
    add_extra_js_url(hass, f"{CARD_URL}?v={version}")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: DengueConfigEntry) -> bool:
    coordinator = DengueCoordinator(hass, entry)
    await coordinator.async_load_cache()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    coordinator.async_start()
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: DengueConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Version 1 had one province and dengue only."""
    if entry.version == 1:
        province = entry.data[CONF_PROVINCE]
        slug = province.lower().replace(" ", "_")

        @callback
        def _new_unique_id(reg_entry: er.RegistryEntry) -> dict | None:
            for key in ("level", "cases_4_weeks", "cases_year"):
                if reg_entry.unique_id == f"{entry.entry_id}_{key}":
                    return {"new_unique_id": f"{entry.entry_id}_{slug}_dengue_{key}"}
            return None

        await er.async_migrate_entries(hass, entry.entry_id, _new_unique_id)
        hass.config_entries.async_update_entry(
            entry, data={CONF_PROVINCES: [province], CONF_DISEASES: ["dengue"]}, version=2
        )
        _LOGGER.info("Migrated %s to version 2 (%s)", entry.title, province)
    return True

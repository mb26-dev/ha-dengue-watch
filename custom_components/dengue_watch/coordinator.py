"""Data update coordinator for Dengue Watch Thailand."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import DengueApi, DengueApiError
from .const import CONF_PROVINCE, DOMAIN, PROVINCES, UPDATE_INTERVAL
from .surveillance import DengueStatus, evaluate

_LOGGER = logging.getLogger(__name__)

type DengueConfigEntry = ConfigEntry["DengueCoordinator"]


class DengueCoordinator(DataUpdateCoordinator[DengueStatus]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=UPDATE_INTERVAL)
        self.province = entry.data[CONF_PROVINCE]
        self.province_th = PROVINCES[self.province]
        self.api = DengueApi(async_get_clientsession(hass), self.province_th)

    async def _async_update_data(self) -> DengueStatus:
        try:
            series = await self.api.weekly()
        except DengueApiError as err:
            raise UpdateFailed(f"DDC surveillance data: {err}") from err
        return evaluate(series, dt_util.now().date())

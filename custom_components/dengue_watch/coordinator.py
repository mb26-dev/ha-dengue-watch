"""Data coordinator: fetches every province / disease pair one after another and keeps a cache."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .api import DengueApi, DengueApiError
from .const import CACHE_VERSION, CONF_DISEASES, CONF_PROVINCES, DOMAIN, PROVINCES, REQUEST_GAP, UPDATE_INTERVAL
from .surveillance import DengueStatus, evaluate

_LOGGER = logging.getLogger(__name__)

type DengueConfigEntry = ConfigEntry["DengueCoordinator"]
Key = tuple[str, str]  # (province, disease)


def entry_provinces(entry: ConfigEntry) -> list[str]:
    return list(entry.options.get(CONF_PROVINCES) or entry.data.get(CONF_PROVINCES) or [])


def entry_diseases(entry: ConfigEntry) -> list[str]:
    return list(entry.options.get(CONF_DISEASES) or entry.data.get(CONF_DISEASES) or ["dengue"])


class DengueCoordinator(DataUpdateCoordinator[dict[Key, DengueStatus]]):
    """Holds one DengueStatus per (province, disease).

    The DDC dashboard needs 5 - 30 s per export, so a full round of e.g. 6 provinces x
    4 diseases takes a few minutes. It runs in the background, publishes every result as
    soon as it arrives, and the weekly series are cached on disk so that a restart shows
    the last values at once.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN)
        self.provinces = entry_provinces(entry)
        self.diseases = entry_diseases(entry)
        self.api = DengueApi(async_get_clientsession(hass))
        self._store: Store[dict[str, Any]] = Store(hass, CACHE_VERSION, f"{DOMAIN}.{entry.entry_id}")
        self._series: dict[Key, dict[int, dict[int, float]]] = {}
        self._fetched: dict[Key, str] = {}
        self._task: asyncio.Task | None = None
        self.last_errors: dict[Key, str] = {}
        self.data = {}

    @property
    def pairs(self) -> list[Key]:
        return [(p, d) for p in self.provinces for d in self.diseases]

    async def async_load_cache(self) -> None:
        cached = await self._store.async_load() or {}
        for item in cached.get("items", []):
            key = (item["province"], item["disease"])
            if key in self.pairs:
                self._series[key] = {int(y): {int(w): v for w, v in weeks.items()} for y, weeks in item["series"].items()}
                self._fetched[key] = item["fetched"]
        self._evaluate_all()

    def _evaluate_all(self) -> None:
        today = dt_util.now().date()
        self.data = {key: evaluate(series, today) for key, series in self._series.items()}

    def fetched_at(self, key: Key) -> str | None:
        return self._fetched.get(key)

    def _stale(self, key: Key) -> bool:
        ts = self._fetched.get(key)
        if not ts:
            return True
        when = dt_util.parse_datetime(ts)
        return when is None or dt_util.utcnow() - when > UPDATE_INTERVAL - timedelta(minutes=10)

    @callback
    def async_start(self) -> None:
        entry = self.config_entry
        entry.async_on_unload(async_track_time_interval(self.hass, self._tick, UPDATE_INTERVAL))
        self._schedule(only_stale=True)

    @callback
    def _tick(self, _now: datetime) -> None:
        self._schedule(only_stale=False)

    @callback
    def _schedule(self, only_stale: bool) -> None:
        if self._task and not self._task.done():
            return
        self._task = self.config_entry.async_create_background_task(
            self.hass, self._refresh_round(only_stale), f"{DOMAIN} refresh"
        )

    async def async_refresh_now(self) -> None:
        self._schedule(only_stale=False)

    async def _refresh_round(self, only_stale: bool) -> None:
        todo = [k for k in self.pairs if not only_stale or self._stale(k)]
        for i, (province, disease) in enumerate(todo):
            if i:
                await asyncio.sleep(REQUEST_GAP)
            try:
                series = await self.api.weekly(PROVINCES[province], disease)
            except DengueApiError as err:
                self.last_errors[(province, disease)] = str(err)
                _LOGGER.warning("DDC export %s / %s failed: %s", province, disease, err)
                continue
            self.last_errors.pop((province, disease), None)
            self._series[(province, disease)] = series
            self._fetched[(province, disease)] = dt_util.utcnow().isoformat()
            self._evaluate_all()
            self.async_set_updated_data(self.data)
        await self._save()

    async def _save(self) -> None:
        items = [
            {"province": p, "disease": d, "fetched": self._fetched.get((p, d)),
             "series": {str(y): {str(w): v for w, v in weeks.items()} for y, weeks in s.items()}}
            for (p, d), s in self._series.items()
        ]
        await self._store.async_save({"items": items})

    async def _async_update_data(self) -> dict[Key, DengueStatus]:
        # manual "update entity" requests: start a round, return what we have
        self._schedule(only_stale=False)
        return self.data

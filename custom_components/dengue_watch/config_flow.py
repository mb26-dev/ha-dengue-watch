"""Config and options flow for Dengue Watch Thailand."""

from __future__ import annotations

from math import cos, hypot, radians
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DengueApi, DengueApiError
from .const import CENTROIDS, CONF_DISEASES, CONF_PROVINCES, DEFAULT_DISEASES, DISEASES, DOMAIN, NEARBY_KM, PROVINCES
from .coordinator import entry_diseases, entry_provinces


def _km(a: tuple[float, float], b: tuple[float, float]) -> float:
    return hypot((a[0] - b[0]) * 111.3 * cos(radians(a[1])), (a[1] - b[1]) * 111.3)


def home_province(lat: float, lon: float) -> str | None:
    best = min(CENTROIDS, key=lambda n: _km((lon, lat), CENTROIDS[n]))
    return best if _km((lon, lat), CENTROIDS[best]) < 150 else None


def nearby(province: str) -> list[str]:
    c = CENTROIDS[province]
    near = sorted((n for n in CENTROIDS if _km(c, CENTROIDS[n]) <= NEARBY_KM), key=lambda n: _km(c, CENTROIDS[n]))
    return [n for n in near if n in PROVINCES]


def _schema(provinces: list[str], diseases: list[str]) -> vol.Schema:
    prov_opts = [selector.SelectOptionDict(value=en, label=f"{en} · {th}") for en, th in PROVINCES.items()]
    dis_opts = [selector.SelectOptionDict(value=k, label=v["name"]) for k, v in DISEASES.items()]
    return vol.Schema({
        vol.Required(CONF_PROVINCES, default=provinces): selector.SelectSelector(
            selector.SelectSelectorConfig(options=prov_opts, multiple=True, mode=selector.SelectSelectorMode.DROPDOWN)),
        vol.Required(CONF_DISEASES, default=diseases): selector.SelectSelector(
            selector.SelectSelectorConfig(options=dis_opts, multiple=True, mode=selector.SelectSelectorMode.LIST)),
    })


async def _validate(hass, provinces: list[str], diseases: list[str]) -> dict[str, str]:
    if not provinces:
        return {CONF_PROVINCES: "no_province"}
    if not diseases:
        return {CONF_DISEASES: "no_disease"}
    try:  # one probe is enough to know that the DDC dashboard answers
        if not await DengueApi(async_get_clientsession(hass)).weekly(PROVINCES[provinces[0]], "dengue"):
            return {"base": "cannot_connect"}
    except DengueApiError:
        return {"base": "cannot_connect"}
    return {}


class DengueWatchConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            provinces, diseases = user_input[CONF_PROVINCES], user_input[CONF_DISEASES]
            errors = await _validate(self.hass, provinces, diseases)
            if not errors:
                await self.async_set_unique_id("_".join(sorted(p.lower().replace(" ", "_") for p in provinces)))
                self._abort_if_unique_id_configured()
                title = provinces[0] if len(provinces) == 1 else f"{provinces[0]} + {len(provinces) - 1}"
                return self.async_create_entry(title=f"Mosquito Watch {title}", data={CONF_PROVINCES: provinces, CONF_DISEASES: diseases})
            provinces_default, diseases_default = provinces, diseases
        else:
            home = home_province(self.hass.config.latitude, self.hass.config.longitude)
            provinces_default = nearby(home) if home else ["Bangkok"]
            diseases_default = DEFAULT_DISEASES
        return self.async_show_form(step_id="user", data_schema=_schema(provinces_default, diseases_default), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return DengueWatchOptionsFlow()


class DengueWatchOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input[CONF_PROVINCES]:
                errors[CONF_PROVINCES] = "no_province"
            elif not user_input[CONF_DISEASES]:
                errors[CONF_DISEASES] = "no_disease"
            else:
                return self.async_create_entry(data=user_input)
        entry = self.config_entry
        return self.async_show_form(step_id="init", data_schema=_schema(entry_provinces(entry), entry_diseases(entry)), errors=errors)

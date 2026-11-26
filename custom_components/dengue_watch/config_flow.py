"""Config flow for Dengue Watch Thailand."""

from __future__ import annotations

from math import cos, radians
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DengueApi, DengueApiError
from .const import CONF_PROVINCE, DOMAIN, PROVINCES

# rough province centres, only used to suggest the province of the Home Assistant location
_CENTRES: dict[str, tuple[float, float]] = {
    "Bangkok": (13.75, 100.5), "Chiang Mai": (18.79, 98.98), "Chiang Rai": (19.91, 99.83),
    "Chonburi": (13.36, 100.98), "Krabi": (8.09, 98.91), "Phang Nga": (8.45, 98.53),
    "Phuket": (7.88, 98.39), "Surat Thani": (9.14, 99.33), "Nakhon Si Thammarat": (8.43, 99.96),
    "Songkhla": (7.19, 100.6), "Trang": (7.56, 99.61), "Satun": (6.62, 100.07),
    "Ranong": (9.96, 98.64), "Chumphon": (10.49, 99.18), "Prachuap Khiri Khan": (11.81, 99.8),
    "Khon Kaen": (16.44, 102.83), "Nakhon Ratchasima": (14.97, 102.1), "Udon Thani": (17.41, 102.79),
    "Ubon Ratchathani": (15.24, 104.85), "Rayong": (12.68, 101.28),
    "Phitsanulok": (16.82, 100.26), "Nonthaburi": (13.86, 100.51), "Samut Prakan": (13.6, 100.6),
    "Pathum Thani": (14.02, 100.53), "Phra Nakhon Si Ayutthaya": (14.35, 100.57),
    "Kanchanaburi": (14.0, 99.55), "Pattani": (6.87, 101.25),
    "Yala": (6.54, 101.28), "Narathiwat": (6.43, 101.82), "Phatthalung": (7.62, 100.08),
}


def _nearest(lat: float, lon: float) -> str | None:
    best, dist = None, 1e9
    for name, (la, lo) in _CENTRES.items():
        if name not in PROVINCES:
            continue
        d = (la - lat) ** 2 + ((lo - lon) * cos(radians(lat))) ** 2
        if d < dist:
            best, dist = name, d
    return best if dist < 1.5 ** 2 else None


class DengueWatchConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            province = user_input[CONF_PROVINCE]
            await self.async_set_unique_id(province.lower().replace(" ", "_"))
            self._abort_if_unique_id_configured()
            try:
                await DengueApi(async_get_clientsession(self.hass), PROVINCES[province]).weekly()
            except DengueApiError:
                errors["base"] = "cannot_connect"
            if not errors:
                return self.async_create_entry(title=f"Dengue {province}", data={CONF_PROVINCE: province})

        default = (user_input or {}).get(CONF_PROVINCE) or _nearest(self.hass.config.latitude, self.hass.config.longitude) or "Bangkok"
        options = [selector.SelectOptionDict(value=en, label=f"{en} · {th}") for en, th in PROVINCES.items()]
        schema = vol.Schema({
            vol.Required(CONF_PROVINCE, default=default): selector.SelectSelector(
                selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN)),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

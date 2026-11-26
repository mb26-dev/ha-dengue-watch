"""Client for the DDC dengue surveillance export."""

from __future__ import annotations

import asyncio
import logging
from urllib.parse import quote

import aiohttp

from .const import BASE_URL, DISEASES, REQUEST_TIMEOUT, USER_AGENT
from .surveillance import SurveillanceParseError, parse_csv

_LOGGER = logging.getLogger(__name__)


class DengueApiError(Exception):
    """The DDC server could not be reached or sent something unexpected."""


def _variants(name: str) -> list[str]:
    """Thai SARA AM can be stored as one character or as NIKHAHIT + SARA AA."""
    alt = name.replace("ำ", "ํา")
    return [name] if alt == name else [name, alt]


class DengueApi:
    def __init__(self, session: aiohttp.ClientSession, province_th: str) -> None:
        self._session = session
        self._province = province_th

    async def _get(self, province: str) -> str:
        url = f"{BASE_URL}?disease={quote(DISEASES)}&chw={quote(province)}"
        try:
            async with self._session.get(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "text/csv"},
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            ) as resp:
                if resp.status != 200:
                    raise DengueApiError(f"HTTP {resp.status}")
                return await resp.text(encoding="utf-8")
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise DengueApiError(str(err) or type(err).__name__) from err

    async def weekly(self) -> dict[int, dict[int, float]]:
        """Weekly dengue cases of the province: {buddhist_year: {week: cases}}."""
        last_error: Exception | None = None
        for name in _variants(self._province):
            text = await self._get(name)
            try:
                series = parse_csv(text)
            except SurveillanceParseError as err:
                last_error = err
                continue
            if any(series.values()):
                return series
            last_error = SurveillanceParseError("export without cases")
        raise DengueApiError(f"no dengue data for {self._province}: {last_error}")

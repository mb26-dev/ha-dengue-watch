"""Client for the DDC surveillance export (Report 506)."""

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
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def _get(self, disease: str, province: str) -> str:
        url = f"{BASE_URL}?disease={quote(DISEASES[disease]['filter'])}&chw={quote(province)}"
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

    async def weekly(self, province_th: str, disease: str = "dengue") -> dict[int, dict[int, float]]:
        """Weekly cases of one disease in one province: {buddhist_year: {week: cases}}.

        A province without any case of a rare disease (e.g. Zika) comes back as an empty
        table; that is a valid answer and returns {}.
        """
        last_error: Exception | None = None
        empty = False
        for name in _variants(province_th):
            text = await self._get(disease, name)
            if text.strip().count("\n") < 1:
                empty = True  # header only or nothing: no case in five years
                continue
            try:
                return parse_csv(text)
            except SurveillanceParseError as err:
                last_error = err
        if empty and last_error is None:
            return {}
        raise DengueApiError(f"no data for {province_th} / {disease}: {last_error}")

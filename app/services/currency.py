import httpx

from app.core.config import settings
from app.core.redis_client import redis_client

_CACHE_KEY = "usd_brl_rate"


async def _fetch_from_awesome() -> float:
    async with httpx.AsyncClient(timeout=5) as client:
        r = await client.get(settings.awesome_api_url)
        r.raise_for_status()
        return float(r.json()["USDBRL"]["bid"])


async def _fetch_from_frankfurter() -> float:
    async with httpx.AsyncClient(timeout=5) as client:
        r = await client.get(settings.frankfurter_api_url)
        r.raise_for_status()
        return float(r.json()["rates"]["BRL"])


async def get_usd_to_brl() -> float:
    cached = await redis_client.get(_CACHE_KEY)
    if cached:
        return float(cached)

    try:
        rate = await _fetch_from_awesome()
    except Exception:
        rate = await _fetch_from_frankfurter()

    await redis_client.setex(_CACHE_KEY, settings.usd_cache_ttl, str(rate))
    return rate

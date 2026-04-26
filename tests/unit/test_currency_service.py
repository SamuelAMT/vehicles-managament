from unittest.mock import AsyncMock, MagicMock, patch

from app.services.currency import get_usd_to_brl


class TestGetUsdToBrl:
    async def test_returns_cached_value(self):
        with patch("app.services.currency.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value="5.25")
            rate = await get_usd_to_brl()
        assert rate == 5.25

    async def test_fetches_from_awesome_when_cache_miss(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"USDBRL": {"bid": "5.30"}}

        with (
            patch("app.services.currency.redis_client") as mock_redis,
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.setex = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            rate = await get_usd_to_brl()

        assert rate == 5.30
        mock_redis.setex.assert_awaited_once()

    async def test_falls_back_to_frankfurter_on_awesome_failure(self):
        frankfurter_response = MagicMock()
        frankfurter_response.json.return_value = {"rates": {"BRL": 5.40}}

        call_count = 0

        async def mock_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("awesome down")
            return frankfurter_response

        with (
            patch("app.services.currency.redis_client") as mock_redis,
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.setex = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value.get = mock_get

            rate = await get_usd_to_brl()

        assert rate == 5.40

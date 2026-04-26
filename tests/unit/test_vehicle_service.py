from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.vehicle import VehicleCreate, VehicleUpdate
from app.services.vehicle import VehicleService


def _make_vehicle(**kwargs):
    v = MagicMock()
    defaults = dict(
        id="1",
        placa="ABC1234",
        marca="Toyota",
        modelo="Corolla",
        ano=2022,
        cor="Branco",
        preco_usd=Decimal("20000.00"),
        ativo=True,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        updated_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    defaults.update(kwargs)
    for k, val in defaults.items():
        setattr(v, k, val)
    return v


def _make_svc(repo_overrides: dict) -> VehicleService:
    svc = VehicleService.__new__(VehicleService)
    repo = AsyncMock()
    for attr, val in repo_overrides.items():
        setattr(repo, attr, val)
    svc.repo = repo
    return svc


class TestCreateVehicle:
    async def test_duplicate_plate_raises_409(self):
        existing = _make_vehicle()
        svc = _make_svc({"get_by_placa": AsyncMock(return_value=existing)})
        with pytest.raises(HTTPException) as exc_info:
            await svc.create_vehicle(
                VehicleCreate(
                    placa="ABC1234", marca="Toyota", modelo="Corolla",
                    ano=2022, cor="Branco", preco_usd=Decimal("20000"),
                )
            )
        assert exc_info.value.status_code == 409

    async def test_new_plate_creates_vehicle(self):
        vehicle = _make_vehicle()
        svc = _make_svc({
            "get_by_placa": AsyncMock(return_value=None),
            "create": AsyncMock(return_value=vehicle),
        })
        with patch("app.services.vehicle.get_usd_to_brl", new=AsyncMock(return_value=5.0)):
            result = await svc.create_vehicle(
                VehicleCreate(placa="XYZ9999", marca="Honda", modelo="Civic", ano=2023, cor="Preto", preco_usd=Decimal("25000"))  # noqa: E501
            )
        assert result.placa == "ABC1234"
        assert result.preco_brl == Decimal("100000.00")


class TestUpdateVehicle:
    async def test_put_missing_fields_raises_422(self):
        vehicle = _make_vehicle()
        svc = _make_svc({"get_by_id": AsyncMock(return_value=vehicle)})
        data = VehicleUpdate(marca="Ford")
        with pytest.raises(HTTPException) as exc_info:
            await svc.update_vehicle("1", data, partial=False)
        assert exc_info.value.status_code == 422

    async def test_patch_partial_update_succeeds(self):
        vehicle = _make_vehicle()
        updated = _make_vehicle(cor="Vermelho")
        svc = _make_svc({
            "get_by_id": AsyncMock(return_value=vehicle),
            "get_by_placa": AsyncMock(return_value=None),
            "update": AsyncMock(return_value=updated),
        })
        with patch("app.services.vehicle.get_usd_to_brl", new=AsyncMock(return_value=5.0)):
            result = await svc.update_vehicle("1", VehicleUpdate(cor="Vermelho"), partial=True)
        assert result.cor == "Vermelho"
        assert result.preco_brl == Decimal("100000.00")

    async def test_update_not_found_raises_404(self):
        svc = _make_svc({"get_by_id": AsyncMock(return_value=None)})
        with pytest.raises(HTTPException) as exc_info:
            await svc.update_vehicle("nonexistent", VehicleUpdate(cor="Azul"), partial=True)
        assert exc_info.value.status_code == 404

    async def test_plate_conflict_on_update_raises_409(self):
        vehicle = _make_vehicle(id="1", placa="ABC1234")
        conflict = _make_vehicle(id="2", placa="XYZ9999")
        svc = _make_svc({
            "get_by_id": AsyncMock(return_value=vehicle),
            "get_by_placa": AsyncMock(return_value=conflict),
        })
        with pytest.raises(HTTPException) as exc_info:
            await svc.update_vehicle("1", VehicleUpdate(placa="XYZ9999"), partial=True)
        assert exc_info.value.status_code == 409


class TestListVehicles:
    async def test_combined_filters_forwarded_to_repo(self):
        svc = _make_svc({"list": AsyncMock(return_value=([], 0))})
        args = ("Toyota", 2022, "Branco", Decimal("10000"), Decimal("30000"), 1, 20, "created_at", "desc")
        with patch("app.services.vehicle.get_usd_to_brl", new=AsyncMock(return_value=5.0)):
            result = await svc.list_vehicles(*args)
        svc.repo.list.assert_awaited_once_with(*args)
        assert result.total == 0

    async def test_invalid_order_by_raises_422(self):
        svc = _make_svc({})
        with pytest.raises(HTTPException) as exc_info:
            await svc.list_vehicles(None, None, None, None, None, 1, 20, "invalid_field", "asc")
        assert exc_info.value.status_code == 422


class TestDeleteVehicle:
    async def test_delete_not_found_raises_404(self):
        svc = _make_svc({"get_by_id": AsyncMock(return_value=None)})
        with pytest.raises(HTTPException) as exc_info:
            await svc.delete_vehicle("nonexistent")
        assert exc_info.value.status_code == 404

    async def test_soft_delete_called(self):
        vehicle = _make_vehicle()
        svc = _make_svc({
            "get_by_id": AsyncMock(return_value=vehicle),
            "soft_delete": AsyncMock(),
        })
        await svc.delete_vehicle("1")
        svc.repo.soft_delete.assert_awaited_once_with(vehicle)

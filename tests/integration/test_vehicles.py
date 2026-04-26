from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import Vehicle
from tests.conftest import TestSession

_VEHICLE_PAYLOAD = {
    "placa": "NEW0001", "marca": "Ford", "modelo": "Focus", "ano": 2021, "cor": "Azul", "preco_usd": "15000.00"
}
_DUP_PAYLOAD = {
    "placa": "DUP0001", "marca": "Ford", "modelo": "Focus", "ano": 2021, "cor": "Azul", "preco_usd": "15000.00"
}


async def _create_vehicle(db: AsyncSession, **kwargs) -> Vehicle:
    defaults = dict(
        placa="TST0001",
        marca="Toyota",
        modelo="Corolla",
        ano=2022,
        cor="Branco",
        preco_usd=Decimal("20000.00"),
    )
    defaults.update(kwargs)
    v = Vehicle(**defaults)
    db.add(v)
    await db.commit()
    return v


class TestAuth:
    async def test_login_valid(self, client: AsyncClient, admin_user):
        r = await client.post("/auth/token", json={"username": "admin", "password": "admin123"})
        assert r.status_code == 200
        assert "access_token" in r.json()

    async def test_login_invalid(self, client: AsyncClient, admin_user):
        r = await client.post("/auth/token", json={"username": "admin", "password": "wrong"})
        assert r.status_code == 401

    async def test_no_token_returns_403(self, client: AsyncClient):
        r = await client.get("/veiculos")
        assert r.status_code == 403


class TestListVehicles:
    async def test_list_returns_paginated(self, client: AsyncClient, db: AsyncSession, user_token: str):
        await _create_vehicle(db, placa="TST0001", marca="Toyota")
        await _create_vehicle(db, placa="TST0002", marca="Honda")
        r = await client.get("/veiculos", headers={"Authorization": f"Bearer {user_token}"})
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    async def test_filter_by_marca(self, client: AsyncClient, db: AsyncSession, user_token: str):
        await _create_vehicle(db, placa="TST0001", marca="Toyota")
        await _create_vehicle(db, placa="TST0002", marca="Honda")
        r = await client.get("/veiculos?marca=Toyota", headers={"Authorization": f"Bearer {user_token}"})
        assert r.status_code == 200
        assert r.json()["total"] == 1

    async def test_filter_by_price_range(self, client: AsyncClient, db: AsyncSession, user_token: str):
        await _create_vehicle(db, placa="TST0001", preco_usd=Decimal("10000"))
        await _create_vehicle(db, placa="TST0002", preco_usd=Decimal("50000"))
        r = await client.get(
            "/veiculos?minPreco=20000&maxPreco=60000",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert r.status_code == 200
        assert r.json()["total"] == 1

    async def test_soft_deleted_not_returned(self, client: AsyncClient, db: AsyncSession, user_token: str):
        v = await _create_vehicle(db, placa="TST0001")
        v.ativo = False
        await db.commit()
        r = await client.get("/veiculos", headers={"Authorization": f"Bearer {user_token}"})
        assert r.json()["total"] == 0


class TestCreateVehicle:
    async def test_admin_can_create(self, client: AsyncClient, admin_token: str):
        r = await client.post(
            "/veiculos",
            json=_VEHICLE_PAYLOAD,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 201
        assert r.json()["placa"] == "NEW0001"

    async def test_user_cannot_create(self, client: AsyncClient, user_token: str):
        r = await client.post(
            "/veiculos",
            json=_VEHICLE_PAYLOAD,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert r.status_code == 403

    async def test_duplicate_plate_returns_409(self, client: AsyncClient, db: AsyncSession, admin_token: str):
        await _create_vehicle(db, placa="DUP0001")
        r = await client.post(
            "/veiculos",
            json=_DUP_PAYLOAD,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 409
        assert r.json()["detail"] == "Plate already registered"

    async def test_deleted_plate_can_be_reused(self, client: AsyncClient, db: AsyncSession, admin_token: str):
        v = await _create_vehicle(db, placa="DUP0001")
        v.ativo = False
        await db.commit()
        r = await client.post(
            "/veiculos",
            json=_DUP_PAYLOAD,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 201

    async def test_no_token_returns_403(self, client: AsyncClient):
        r = await client.post("/veiculos", json={})
        assert r.status_code in (401, 403)


class TestUpdateVehicle:
    async def test_put_requires_all_fields(self, client: AsyncClient, db: AsyncSession, admin_token: str):
        v = await _create_vehicle(db)
        r = await client.put(
            f"/veiculos/{v.id}",
            json={"marca": "Honda"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 422

    async def test_patch_partial_update(self, client: AsyncClient, db: AsyncSession, admin_token: str):
        v = await _create_vehicle(db)
        r = await client.patch(
            f"/veiculos/{v.id}",
            json={"cor": "Vermelho"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        assert r.json()["cor"] == "Vermelho"

    async def test_user_cannot_update(self, client: AsyncClient, db: AsyncSession, user_token: str):
        v = await _create_vehicle(db)
        r = await client.patch(
            f"/veiculos/{v.id}",
            json={"cor": "Verde"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert r.status_code == 403


class TestDeleteVehicle:
    async def test_admin_soft_deletes(self, client: AsyncClient, db: AsyncSession, admin_token: str):
        v = await _create_vehicle(db)
        r = await client.delete(f"/veiculos/{v.id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 204
        async with TestSession() as fresh:
            refreshed = await fresh.get(Vehicle, v.id)
            assert refreshed.ativo is False

    async def test_user_cannot_delete(self, client: AsyncClient, db: AsyncSession, user_token: str):
        v = await _create_vehicle(db)
        r = await client.delete(f"/veiculos/{v.id}", headers={"Authorization": f"Bearer {user_token}"})
        assert r.status_code == 403


class TestReports:
    async def test_report_by_brand(self, client: AsyncClient, db: AsyncSession, user_token: str):
        await _create_vehicle(db, placa="T001", marca="Toyota")
        await _create_vehicle(db, placa="T002", marca="Toyota")
        await _create_vehicle(db, placa="H001", marca="Honda")
        r = await client.get("/veiculos/relatorios/por-marca", headers={"Authorization": f"Bearer {user_token}"})
        assert r.status_code == 200
        data = r.json()
        assert data[0]["marca"] == "Toyota"
        assert data[0]["total"] == 2

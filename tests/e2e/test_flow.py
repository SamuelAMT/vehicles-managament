from httpx import AsyncClient

from app.models.user import User

_BMW = {"placa": "E2E0001", "marca": "BMW", "modelo": "320i", "ano": 2023, "cor": "Preto", "preco_usd": "45000.00"}
_AUDI = {"placa": "E2E0002", "marca": "Audi", "modelo": "A4", "ano": 2022, "cor": "Branco", "preco_usd": "50000.00"}


class TestFullFlow:
    async def test_obtain_token_create_list_filter_detail(
        self, client: AsyncClient, admin_user: User, regular_user: User
    ):
        r = await client.post("/auth/token", json={"username": "admin", "password": "admin123"})
        assert r.status_code == 200
        admin_token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}

        r = await client.post("/veiculos", json=_BMW, headers=headers)
        assert r.status_code == 201
        vehicle_id = r.json()["id"]

        r = await client.post("/veiculos", json=_AUDI, headers=headers)
        assert r.status_code == 201

        r = await client.post("/auth/token", json={"username": "user1", "password": "user123"})
        assert r.status_code == 200
        user_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

        r = await client.get("/veiculos", headers=user_headers)
        assert r.status_code == 200
        assert r.json()["total"] == 2

        r = await client.get("/veiculos?marca=BMW", headers=user_headers)
        assert r.status_code == 200
        assert r.json()["total"] == 1
        assert r.json()["items"][0]["marca"] == "BMW"

        r = await client.get(f"/veiculos/{vehicle_id}", headers=user_headers)
        assert r.status_code == 200
        assert r.json()["placa"] == "E2E0001"

        r = await client.get("/veiculos/relatorios/por-marca", headers=user_headers)
        assert r.status_code == 200
        marcas = {item["marca"] for item in r.json()}
        assert "BMW" in marcas and "Audi" in marcas

        r = await client.delete(f"/veiculos/{vehicle_id}", headers=user_headers)
        assert r.status_code == 403

        r = await client.delete(f"/veiculos/{vehicle_id}", headers=headers)
        assert r.status_code == 204

        r = await client.get(f"/veiculos/{vehicle_id}", headers=user_headers)
        assert r.status_code == 404

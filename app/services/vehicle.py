from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import Vehicle
from app.repositories.vehicle import VehicleRepository
from app.schemas.common import PaginatedResponse
from app.schemas.vehicle import BrandReportItem, VehicleCreate, VehicleResponse, VehicleUpdate
from app.services.currency import get_usd_to_brl

_SORTABLE = {"placa", "marca", "modelo", "ano", "cor", "preco_usd", "created_at"}


class VehicleService:
    def __init__(self, db: AsyncSession):
        self.repo = VehicleRepository(db)

    async def _to_response(self, vehicle: Vehicle) -> VehicleResponse:
        rate = await get_usd_to_brl()
        return VehicleResponse(
            id=vehicle.id,
            placa=vehicle.placa,
            marca=vehicle.marca,
            modelo=vehicle.modelo,
            ano=vehicle.ano,
            cor=vehicle.cor,
            preco_usd=vehicle.preco_usd,
            preco_brl=round(vehicle.preco_usd * Decimal(str(rate)), 2),
            ativo=vehicle.ativo,
            created_at=vehicle.created_at,
            updated_at=vehicle.updated_at,
        )

    async def list_vehicles(
        self,
        marca: str | None,
        ano: int | None,
        cor: str | None,
        min_preco: Decimal | None,
        max_preco: Decimal | None,
        page: int,
        page_size: int,
        order_by: str,
        order_dir: str,
    ) -> PaginatedResponse[VehicleResponse]:
        if order_by not in _SORTABLE:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"order_by must be one of {_SORTABLE}",
            )
        if order_dir not in ("asc", "desc"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="order_dir must be 'asc' or 'desc'",
            )

        vehicles, total = await self.repo.list(
            marca, ano, cor, min_preco, max_preco, page, page_size, order_by, order_dir
        )
        rate = await get_usd_to_brl()
        items = [
            VehicleResponse(
                id=v.id,
                placa=v.placa,
                marca=v.marca,
                modelo=v.modelo,
                ano=v.ano,
                cor=v.cor,
                preco_usd=v.preco_usd,
                preco_brl=round(v.preco_usd * Decimal(str(rate)), 2),
                ativo=v.ativo,
                created_at=v.created_at,
                updated_at=v.updated_at,
            )
            for v in vehicles
        ]
        return PaginatedResponse(total=total, page=page, page_size=page_size, items=items)

    async def get_vehicle(self, vehicle_id: str) -> VehicleResponse:
        vehicle = await self.repo.get_by_id(vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
        return await self._to_response(vehicle)

    async def create_vehicle(self, data: VehicleCreate) -> VehicleResponse:
        if await self.repo.get_by_placa(data.placa):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Plate already registered")
        vehicle = await self.repo.create(data)
        return await self._to_response(vehicle)

    async def update_vehicle(self, vehicle_id: str, data: VehicleUpdate, partial: bool = False) -> VehicleResponse:
        vehicle = await self.repo.get_by_id(vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

        if not partial:
            missing = [f for f in ("placa", "marca", "modelo", "ano", "cor", "preco_usd") if getattr(data, f) is None]
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"PUT requires all fields; missing: {missing}",
                )

        if data.placa and data.placa != vehicle.placa:
            if await self.repo.get_by_placa(data.placa, exclude_id=vehicle_id):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Plate already registered")

        updated = await self.repo.update(vehicle, data)
        return await self._to_response(updated)

    async def delete_vehicle(self, vehicle_id: str) -> None:
        vehicle = await self.repo.get_by_id(vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
        await self.repo.soft_delete(vehicle)

    async def report_by_brand(self) -> list[BrandReportItem]:
        return await self.repo.report_by_brand()

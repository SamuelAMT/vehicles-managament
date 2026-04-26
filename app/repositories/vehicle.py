from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import Vehicle
from app.schemas.vehicle import BrandReportItem, VehicleCreate, VehicleUpdate


class VehicleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, vehicle_id: str) -> Vehicle | None:
        result = await self.db.execute(
            select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.ativo == True)  # noqa: E712
        )
        return result.scalar_one_or_none()

    async def get_by_placa(self, placa: str, exclude_id: str | None = None) -> Vehicle | None:
        q = select(Vehicle).where(Vehicle.placa == placa, Vehicle.ativo == True)  # noqa: E712
        if exclude_id:
            q = q.where(Vehicle.id != exclude_id)
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def list(
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
    ) -> tuple[list[Vehicle], int]:
        q = select(Vehicle).where(Vehicle.ativo == True)  # noqa: E712

        if marca:
            q = q.where(Vehicle.marca.ilike(f"%{marca}%"))
        if ano:
            q = q.where(Vehicle.ano == ano)
        if cor:
            q = q.where(Vehicle.cor.ilike(f"%{cor}%"))
        if min_preco is not None:
            q = q.where(Vehicle.preco_usd >= min_preco)
        if max_preco is not None:
            q = q.where(Vehicle.preco_usd <= max_preco)

        count_q = select(func.count()).select_from(q.subquery())
        total = (await self.db.execute(count_q)).scalar_one()

        col = getattr(Vehicle, order_by, Vehicle.created_at)
        q = q.order_by(col.desc() if order_dir == "desc" else col.asc())
        q = q.offset((page - 1) * page_size).limit(page_size)

        rows = (await self.db.execute(q)).scalars().all()
        return list(rows), total

    async def create(self, data: VehicleCreate) -> Vehicle:
        vehicle = Vehicle(**data.model_dump())
        self.db.add(vehicle)
        await self.db.commit()
        await self.db.refresh(vehicle)
        return vehicle

    async def update(self, vehicle: Vehicle, data: VehicleUpdate) -> Vehicle:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(vehicle, field, value)
        await self.db.commit()
        await self.db.refresh(vehicle)
        return vehicle

    async def soft_delete(self, vehicle: Vehicle) -> None:
        vehicle.ativo = False
        await self.db.commit()

    async def report_by_brand(self) -> list[BrandReportItem]:
        q = (
            select(Vehicle.marca, func.count(Vehicle.id).label("total"))
            .where(Vehicle.ativo == True)  # noqa: E712
            .group_by(Vehicle.marca)
            .order_by(func.count(Vehicle.id).desc())
        )
        rows = (await self.db.execute(q)).all()
        return [BrandReportItem(marca=row.marca, total=row.total) for row in rows]

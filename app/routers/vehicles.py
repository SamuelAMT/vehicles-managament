from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user, require_admin
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.vehicle import BrandReportItem, VehicleCreate, VehicleResponse, VehicleUpdate
from app.services.vehicle import VehicleService

router = APIRouter(prefix="/veiculos", tags=["vehicles"])


def _svc(db: AsyncSession = Depends(get_db)) -> VehicleService:
    return VehicleService(db)


@router.get("/relatorios/por-marca", response_model=list[BrandReportItem])
async def report_by_brand(
    _: User = Depends(get_current_user),
    svc: VehicleService = Depends(_svc),
):
    return await svc.report_by_brand()


@router.get("", response_model=PaginatedResponse[VehicleResponse])
async def list_vehicles(
    marca: str | None = Query(None),
    ano: int | None = Query(None),
    cor: str | None = Query(None),
    minPreco: Decimal | None = Query(None),
    maxPreco: Decimal | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = Query("created_at"),
    order_dir: str = Query("desc"),
    _: User = Depends(get_current_user),
    svc: VehicleService = Depends(_svc),
):
    return await svc.list_vehicles(marca, ano, cor, minPreco, maxPreco, page, page_size, order_by, order_dir)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: str,
    _: User = Depends(get_current_user),
    svc: VehicleService = Depends(_svc),
):
    return await svc.get_vehicle(vehicle_id)


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    body: VehicleCreate,
    _: User = Depends(require_admin),
    svc: VehicleService = Depends(_svc),
):
    return await svc.create_vehicle(body)


@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: str,
    body: VehicleUpdate,
    _: User = Depends(require_admin),
    svc: VehicleService = Depends(_svc),
):
    return await svc.update_vehicle(vehicle_id, body, partial=False)


@router.patch("/{vehicle_id}", response_model=VehicleResponse)
async def partial_update_vehicle(
    vehicle_id: str,
    body: VehicleUpdate,
    _: User = Depends(require_admin),
    svc: VehicleService = Depends(_svc),
):
    return await svc.update_vehicle(vehicle_id, body, partial=True)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: str,
    _: User = Depends(require_admin),
    svc: VehicleService = Depends(_svc),
):
    await svc.delete_vehicle(vehicle_id)

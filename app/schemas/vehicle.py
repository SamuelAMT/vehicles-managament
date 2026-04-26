from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class VehicleCreate(BaseModel):
    placa: str = Field(..., min_length=7, max_length=10)
    marca: str = Field(..., min_length=1, max_length=100)
    modelo: str = Field(..., min_length=1, max_length=100)
    ano: int = Field(..., ge=1886, le=2100)
    cor: str = Field(..., min_length=1, max_length=50)
    preco_usd: Decimal = Field(..., gt=0, decimal_places=2)

    @field_validator("placa")
    @classmethod
    def normalize_placa(cls, v: str) -> str:
        return v.upper().strip()


class VehicleUpdate(BaseModel):
    placa: str | None = Field(None, min_length=7, max_length=10)
    marca: str | None = Field(None, min_length=1, max_length=100)
    modelo: str | None = Field(None, min_length=1, max_length=100)
    ano: int | None = Field(None, ge=1886, le=2100)
    cor: str | None = Field(None, min_length=1, max_length=50)
    preco_usd: Decimal | None = Field(None, gt=0, decimal_places=2)

    @field_validator("placa")
    @classmethod
    def normalize_placa(cls, v: str | None) -> str | None:
        return v.upper().strip() if v else v


class VehicleResponse(BaseModel):
    id: str
    placa: str
    marca: str
    modelo: str
    ano: int
    cor: str
    preco_usd: Decimal
    preco_brl: Decimal
    ativo: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VehicleFilter(BaseModel):
    marca: str | None = None
    ano: int | None = None
    cor: str | None = None
    min_preco: Decimal | None = Field(None, alias="minPreco")
    max_preco: Decimal | None = Field(None, alias="maxPreco")

    model_config = {"populate_by_name": True}


class BrandReportItem(BaseModel):
    marca: str
    total: int

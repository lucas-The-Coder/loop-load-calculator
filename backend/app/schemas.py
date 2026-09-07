from typing import List, Optional

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
)


# ---------------------------------------------------------------------------
# Device schemas
# ---------------------------------------------------------------------------

class DeviceCreateSchema(BaseModel):

    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    quantity: int = Field(
        default=1,
        ge=1,
    )

    standby_current_ma: float = Field(
        ...,
        ge=0,
    )

    alarm_current_ma: float = Field(
        ...,
        ge=0,
    )

    address: Optional[str] = Field(
        default=None,
        max_length=50,
    )

    notes: str = Field(
        default="",
        max_length=500,
    )


class DeviceSchema(DeviceCreateSchema):

    id: Optional[int] = Field(
        default=None,
    )

    total_standby_current_ma: float = Field(
        default=0.0,
        ge=0,
    )

    total_alarm_current_ma: float = Field(
        default=0.0,
        ge=0,
    )


# ---------------------------------------------------------------------------
# Cable schemas
# ---------------------------------------------------------------------------

class CableSchema(BaseModel):

    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    cable_type: str = Field(
        default="",
        max_length=100,
    )

    length_m: float = Field(
        default=0.0,
        ge=0,
    )

    resistance_per_metre_ohm: float = Field(
        default=0.0,
        ge=0,
    )

    conductor_count: int = Field(
        default=2,
        ge=1,
    )


# ---------------------------------------------------------------------------
# Loop configuration
# ---------------------------------------------------------------------------

class LoopConfigurationSchema(BaseModel):

    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    name: str = Field(
        default="Loop 1",
        min_length=1,
        max_length=100,
    )

    capacity_ma: float = Field(
        ...,
        gt=0,
    )

    supply_voltage_v: float = Field(
        ...,
        gt=0,
    )

    minimum_device_voltage_v: float = Field(
        default=0.0,
        ge=0,
    )

    cable: Optional[CableSchema] = None


# ---------------------------------------------------------------------------
# Loop schemas
# ---------------------------------------------------------------------------

class LoopCreateSchema(BaseModel):

    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    configuration: LoopConfigurationSchema

    devices: List[DeviceCreateSchema] = Field(
        default_factory=list,
    )


class LoopSchema(LoopCreateSchema):

    id: Optional[int] = None

    device_count: int = Field(
        default=0,
        ge=0,
    )


# ---------------------------------------------------------------------------
# Calculation request
# ---------------------------------------------------------------------------

class LoopCalculationRequest(BaseModel):

    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    loop: LoopCreateSchema


# ---------------------------------------------------------------------------
# Load results
# ---------------------------------------------------------------------------

class LoadResultSchema(BaseModel):

    capacity_ma: float = Field(
        ...,
        ge=0,
    )

    standby_load_ma: float = Field(
        ...,
        ge=0,
    )

    alarm_load_ma: float = Field(
        ...,
        ge=0,
    )

    standby_remaining_ma: float

    alarm_remaining_ma: float

    standby_percentage: float = Field(
        ...,
        ge=0,
    )

    alarm_percentage: float = Field(
        ...,
        ge=0,
    )

    standby_overload: bool

    alarm_overload: bool

    within_capacity: bool


# ---------------------------------------------------------------------------
# Voltage-drop results
# ---------------------------------------------------------------------------

class VoltageDropResultSchema(BaseModel):

    supply_voltage_v: float = Field(
        ...,
        ge=0,
    )

    current_ma: float = Field(
        ...,
        ge=0,
    )

    cable_resistance_ohm: float = Field(
        ...,
        ge=0,
    )

    voltage_drop_v: float = Field(
        ...,
        ge=0,
    )

    end_voltage_v: float

    minimum_voltage_v: float = Field(
        default=0.0,
        ge=0,
    )

    voltage_margin_v: float

    voltage_ok: bool


# ---------------------------------------------------------------------------
# Complete calculation result
# ---------------------------------------------------------------------------

class CalculationResultSchema(BaseModel):

    loop_name: str

    load: LoadResultSchema

    standby_voltage: Optional[
        VoltageDropResultSchema
    ] = None

    alarm_voltage: Optional[
        VoltageDropResultSchema
    ] = None

    warnings: List[str] = Field(
        default_factory=list,
    )

    passed: bool


# ---------------------------------------------------------------------------
# Project schemas
# ---------------------------------------------------------------------------

class ProjectCreateSchema(BaseModel):

    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    name: str = Field(
        default="ZP3 Project",
        min_length=1,
        max_length=150,
    )

    panel_model: str = Field(
        default="ZP3",
        min_length=1,
        max_length=100,
    )

    loops: List[LoopCreateSchema] = Field(
        default_factory=list,
    )

    notes: str = Field(
        default="",
        max_length=2000,
    )


class ProjectSchema(ProjectCreateSchema):

    id: Optional[int] = None

    loop_count: int = Field(
        default=0,
        ge=0,
    )


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_loop_request(
    request: LoopCalculationRequest,
) -> LoopCalculationRequest:

    if not request.loop.devices:
        raise ValueError(
            "At least one device is required "
            "for a loop calculation."
        )

    return request


def validate_project(
    project: ProjectCreateSchema,
) -> ProjectCreateSchema:

    if not project.loops:
        raise ValueError(
            "A project must contain at least one loop."
        )

    return project

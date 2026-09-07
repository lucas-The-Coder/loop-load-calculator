from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Device schemas
# ---------------------------------------------------------------------------

class DeviceCreateSchema(BaseModel):
    """Schema used when adding a device to a loop."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Device name or device type.",
    )

    quantity: int = Field(
        default=1,
        ge=1,
        description="Number of identical devices.",
    )

    standby_current_ma: float = Field(
        ...,
        ge=0,
        description="Standby current per device in mA.",
    )

    alarm_current_ma: float = Field(
        ...,
        ge=0,
        description="Alarm current per device in mA.",
    )

    address: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Optional device address or address range.",
    )

    notes: str = Field(
        default="",
        max_length=500,
        description="Optional notes.",
    )


class DeviceSchema(DeviceCreateSchema):
    """Schema representing a device returned by the application."""

    id: Optional[int] = Field(
        default=None,
        description="Optional database/application identifier.",
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
    """Schema containing loop cable information."""

    model_config = ConfigDict(str_strip_whitespace=True)

    cable_type: str = Field(
        default="",
        max_length=100,
        description="Cable type/reference.",
    )

    length_m: float = Field(
        default=0.0,
        ge=0,
        description="Cable length in metres.",
    )

    resistance_per_metre_ohm: float = Field(
        default=0.0,
        ge=0,
        description="Resistance of one conductor in ohms per metre.",
    )

    conductor_count: int = Field(
        default=2,
        ge=1,
        description="Number of conductors in the current path.",
    )


# ---------------------------------------------------------------------------
# Loop configuration schemas
# ---------------------------------------------------------------------------

class LoopConfigurationSchema(BaseModel):
    """Schema containing the electrical configuration of a loop."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        default="Loop 1",
        min_length=1,
        max_length=100,
    )

    capacity_ma: float = Field(
        ...,
        gt=0,
        description="Maximum loop current in mA.",
    )

    supply_voltage_v: float = Field(
        ...,
        gt=0,
        description="Loop supply voltage in volts.",
    )

    minimum_device_voltage_v: float = Field(
        default=0.0,
        ge=0,
        description="Minimum acceptable device voltage.",
    )

    cable: Optional[CableSchema] = None


# ---------------------------------------------------------------------------
# Loop schemas
# ---------------------------------------------------------------------------

class LoopCreateSchema(BaseModel):
    """Schema used to create a loop."""

    model_config = ConfigDict(str_strip_whitespace=True)

    configuration: LoopConfigurationSchema

    devices: List[DeviceCreateSchema] = Field(
        default_factory=list,
    )


class LoopSchema(LoopCreateSchema):
    """Schema representing a complete loop."""

    id: Optional[int] = Field(
        default=None,
        description="Optional loop identifier.",
    )

    device_count: int = Field(
        default=0,
        ge=0,
    )


# ---------------------------------------------------------------------------
# Calculation request schemas
# ---------------------------------------------------------------------------

class LoopCalculationRequest(BaseModel):
    """
    Input schema for performing a loop calculation.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    loop: LoopCreateSchema


# ---------------------------------------------------------------------------
# Load result schemas
# ---------------------------------------------------------------------------

class LoadResultSchema(BaseModel):
    """Schema containing calculated current-load results."""

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
# Voltage-drop result schemas
# ---------------------------------------------------------------------------

class VoltageDropResultSchema(BaseModel):
    """Schema containing voltage-drop calculation results."""

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
    """Schema returned after a complete loop calculation."""

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
    """Schema used when creating a project."""

    model_config = ConfigDict(str_strip_whitespace=True)

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
    """Schema representing a complete project."""

    id: Optional[int] = Field(
        default=None,
    )

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
    """
    Validate a loop calculation request.

    Pydantic performs the field-level validation automatically.
    This function provides a single place for additional
    application-specific validation later.
    """

    loop = request.loop

    if not loop.devices:
        raise ValueError(
            "At least one device is required for a loop calculation."
        )

    return request


def validate_project(
    project: ProjectCreateSchema,
) -> ProjectCreateSchema:
    """
    Validate a project before processing or saving it.
    """

    if not project.loops:
        raise ValueError(
            "A project must contain at least one loop."
        )

    return project
# backend/app/models.py

"""
Domain models for the ZP3 Loop Load Calculator.
"""

from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Device
# ---------------------------------------------------------------------------

@dataclass
class Device:
    """A device connected to a ZP3 loop."""

    name: str
    quantity: int = 1

    standby_current_ma: float = 0.0
    alarm_current_ma: float = 0.0

    address: Optional[str] = None
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError(
                "Device name cannot be empty."
            )

        if self.quantity < 1:
            raise ValueError(
                "Device quantity must be at least 1."
            )

        if self.standby_current_ma < 0:
            raise ValueError(
                "Standby current cannot be negative."
            )

        if self.alarm_current_ma < 0:
            raise ValueError(
                "Alarm current cannot be negative."
            )


# ---------------------------------------------------------------------------
# Cable
# ---------------------------------------------------------------------------

@dataclass
class Cable:
    """Cable information used for voltage-drop calculations."""

    cable_type: Optional[str] = None

    length_m: float = 0.0

    resistance_per_metre_ohm: float = 0.0

    conductor_count: int = 2

    def __post_init__(self) -> None:
        if self.length_m < 0:
            raise ValueError(
                "Cable length cannot be negative."
            )

        if self.resistance_per_metre_ohm < 0:
            raise ValueError(
                "Cable resistance cannot be negative."
            )

        if self.conductor_count < 1:
            raise ValueError(
                "Conductor count must be at least 1."
            )


# ---------------------------------------------------------------------------
# Loop
# ---------------------------------------------------------------------------

@dataclass
class Loop:
    """A ZP3 detection loop."""

    name: str

    capacity_ma: float

    supply_voltage_v: float

    minimum_device_voltage_v: float = 0.0

    devices: List[Device] = field(
        default_factory=list
    )

    cable: Optional[Cable] = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError(
                "Loop name cannot be empty."
            )

        if self.capacity_ma <= 0:
            raise ValueError(
                "Loop capacity must be greater than zero."
            )

        if self.supply_voltage_v <= 0:
            raise ValueError(
                "Supply voltage must be greater than zero."
            )

        if self.minimum_device_voltage_v < 0:
            raise ValueError(
                "Minimum device voltage cannot be negative."
            )

    def add_device(self, device: Device) -> None:
        """Add a device to the loop."""

        self.devices.append(device)

    def remove_device(self, index: int) -> None:
        """Remove a device by list index."""

        if index < 0 or index >= len(self.devices):
            raise IndexError(
                "Device index is out of range."
            )

        self.devices.pop(index)


# ---------------------------------------------------------------------------
# Load result
# ---------------------------------------------------------------------------

@dataclass
class LoadResult:
    """Result of the loop current/load calculation."""

    capacity_ma: float

    standby_load_ma: float
    alarm_load_ma: float

    standby_remaining_ma: float
    alarm_remaining_ma: float

    standby_percentage: float
    alarm_percentage: float

    standby_overload: bool
    alarm_overload: bool

    @property
    def within_capacity(self) -> bool:
        """Return True when both standby and alarm loads are within capacity."""

        return not (
            self.standby_overload
            or self.alarm_overload
        )


# ---------------------------------------------------------------------------
# Voltage-drop result
# ---------------------------------------------------------------------------

@dataclass
class VoltageDropResult:
    """Result of a loop voltage-drop calculation."""

    supply_voltage_v: float

    current_ma: float

    cable_resistance_ohm: float

    voltage_drop_v: float

    end_voltage_v: float

    minimum_voltage_v: float

    @property
    def voltage_margin_v(self) -> float:
        """Voltage remaining above the minimum required voltage."""

        return (
            self.end_voltage_v
            - self.minimum_voltage_v
        )

    @property
    def voltage_ok(self) -> bool:
        """Return True when end voltage meets the minimum requirement."""

        return (
            self.end_voltage_v
            >= self.minimum_voltage_v
        )

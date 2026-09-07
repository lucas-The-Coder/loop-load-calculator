from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Device:
    """
    Represents a device installed on a ZP3 loop.

    Current values are specified in milliamps (mA).
    """

    name: str
    quantity: int = 1
    standby_current_ma: float = 0.0
    alarm_current_ma: float = 0.0
    address: Optional[str] = None
    notes: str = ""

    def __post_init__(self) -> None:
        if self.quantity < 1:
            raise ValueError("Device quantity must be at least 1.")

        if self.standby_current_ma < 0:
            raise ValueError(
                "Standby current cannot be negative."
            )

        if self.alarm_current_ma < 0:
            raise ValueError(
                "Alarm current cannot be negative."
            )

    @property
    def total_standby_current_ma(self) -> float:
        """Total standby current for all devices of this type."""
        return self.quantity * self.standby_current_ma

    @property
    def total_alarm_current_ma(self) -> float:
        """Total alarm current for all devices of this type."""
        return self.quantity * self.alarm_current_ma


@dataclass
class Cable:
    """
    Represents loop cable information.

    Resistance is specified in ohms per metre.
    """

    cable_type: str = ""
    length_m: float = 0.0
    resistance_per_metre_ohm: float = 0.0
    conductor_count: int = 2

    def __post_init__(self) -> None:
        if self.length_m < 0:
            raise ValueError("Cable length cannot be negative.")

        if self.resistance_per_metre_ohm < 0:
            raise ValueError(
                "Cable resistance cannot be negative."
            )

        if self.conductor_count < 1:
            raise ValueError(
                "Conductor count must be at least 1."
            )

    @property
    def total_resistance_ohm(self) -> float:
        """Return the total cable resistance."""

        return (
            self.resistance_per_metre_ohm
            * self.length_m
            * self.conductor_count
        )


@dataclass
class LoopConfiguration:
    """
    Configuration for a single ZP3 loop.
    """

    name: str = "Loop 1"

    # These values must be set according to the applicable
    # ZP3 panel/module specifications.
    capacity_ma: float = 500.0

    supply_voltage_v: float = 24.0

    # Minimum voltage required by the devices on the loop.
    minimum_device_voltage_v: float = 0.0

    cable: Optional[Cable] = None

    def __post_init__(self) -> None:
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


@dataclass
class Loop:
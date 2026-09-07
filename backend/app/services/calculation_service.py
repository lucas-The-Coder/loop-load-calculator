from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class DeviceLoad:
    """Electrical load information for one device type."""

    name: str
    quantity: int
    standby_ma: float
    alarm_ma: float

    @property
    def standby_total_ma(self) -> float:
        """Return the total standby current for this device type."""
        return self.quantity * self.standby_ma

    @property
    def alarm_total_ma(self) -> float:
        """Return the total alarm current for this device type."""
        return self.quantity * self.alarm_ma


@dataclass(frozen=True)
class LoopLoadResult:
    """Calculated loop load results."""

    capacity_ma: float
    standby_load_ma: float
    alarm_load_ma: float

    @property
    def standby_remaining_ma(self) -> float:
        return self.capacity_ma - self.standby_load_ma

    @property
    def alarm_remaining_ma(self) -> float:
        return self.capacity_ma - self.alarm_load_ma

    @property
    def standby_percentage(self) -> float:
        return percentage_of(self.standby_load_ma, self.capacity_ma)

    @property
    def alarm_percentage(self) -> float:
        return percentage_of(self.alarm_load_ma, self.capacity_ma)

    @property
    def standby_overload(self) -> bool:
        return self.standby_load_ma > self.capacity_ma

    @property
    def alarm_overload(self) -> bool:
        return self.alarm_load_ma > self.capacity_ma

    @property
    def is_within_capacity(self) -> bool:
        return not self.standby_overload and not self.alarm_overload


def validate_device(device: DeviceLoad) -> None:
    """Validate a device load definition."""

    if not device.name.strip():
        raise ValueError("Device name cannot be empty.")

    if device.quantity < 1:
        raise ValueError("Device quantity must be at least 1.")

    if device.standby_ma < 0:
        raise ValueError("Standby current cannot be negative.")

    if device.alarm_ma < 0:
        raise ValueError("Alarm current cannot be negative.")


def validate_capacity(capacity_ma: float) -> None:
    """Validate loop capacity."""

    if capacity_ma <= 0:
        raise ValueError("Loop capacity must be greater than zero.")


def percentage_of(value: float, total: float) -> float:
    """Calculate value as a percentage of total."""

    if total <= 0:
        raise ValueError("Percentage denominator must be greater than zero.")

    return (value / total) * 100.0


def calculate_device_load(device: DeviceLoad) -> tuple[float, float]:
    """
    Calculate the total standby and alarm load for one device type.

    Returns:
        (standby_current_ma, alarm_current_ma)
    """

    validate_device(device)

    return (
        device.standby_total_ma,
        device.alarm_total_ma,
    )


def calculate_loop_load(
    devices: Iterable[DeviceLoad],
    capacity_ma: float,
) -> LoopLoadResult:

    validate_capacity(cap)
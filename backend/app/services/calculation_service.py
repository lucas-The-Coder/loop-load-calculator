# backend/app/services/calculation_service.py

"""
Calculation service for the ZP3 loop load calculator.
"""

from typing import Iterable

from ..models import (
    Device,
    LoadResult,
    VoltageDropResult,
)


# ---------------------------------------------------------------------------
# Device load calculations
# ---------------------------------------------------------------------------

def calculate_device_standby_load(
    device: Device,
) -> float:
    """
    Calculate total standby current for a device type.
    """

    return (
        device.quantity
        * device.standby_current_ma
    )


def calculate_device_alarm_load(
    device: Device,
) -> float:
    """
    Calculate total alarm current for a device type.
    """

    return (
        device.quantity
        * device.alarm_current_ma
    )


# ---------------------------------------------------------------------------
# Total loop load
# ---------------------------------------------------------------------------

def calculate_total_standby_load(
    devices: Iterable[Device],
) -> float:
    """
    Calculate total standby loop current.
    """

    return sum(
        calculate_device_standby_load(device)
        for device in devices
    )


def calculate_total_alarm_load(
    devices: Iterable[Device],
) -> float:
    """
    Calculate total alarm loop current.
    """

    return sum(
        calculate_device_alarm_load(device)
        for device in devices
    )


# ---------------------------------------------------------------------------
# Percentage calculations
# ---------------------------------------------------------------------------

def calculate_percentage(
    value: float,
    maximum: float,
) -> float:
    """
    Calculate a value as a percentage of a maximum.
    """

    if maximum <= 0:
        raise ValueError(
            "Maximum value must be greater than zero."
        )

    return (value / maximum) * 100.0


# ---------------------------------------------------------------------------
# Loop load
# ---------------------------------------------------------------------------

def calculate_loop_load(
    devices: Iterable[Device],
    capacity_ma: float,
) -> LoadResult:
    """
    Calculate complete loop load.
    """

    if capacity_ma <= 0:
        raise ValueError(
            "Loop capacity must be greater than zero."
        )

    devices = list(devices)

    standby_load = calculate_total_standby_load(
        devices
    )

    alarm_load = calculate_total_alarm_load(
        devices
    )

    standby_remaining = (
        capacity_ma - standby_load
    )

    alarm_remaining = (
        capacity_ma - alarm_load
    )

    standby_percentage = calculate_percentage(
        standby_load,
        capacity_ma,
    )

    alarm_percentage = calculate_percentage(
        alarm_load,
        capacity_ma,
    )

    return LoadResult(
        capacity_ma=capacity_ma,

        standby_load_ma=standby_load,

        alarm_load_ma=alarm_load,

        standby_remaining_ma=standby_remaining,

        alarm_remaining_ma=alarm_remaining,

        standby_percentage=standby_percentage,

        alarm_percentage=alarm_percentage,

        standby_overload=(
            standby_load > capacity_ma
        ),

        alarm_overload=(
            alarm_load > capacity_ma
        ),
    )


# ---------------------------------------------------------------------------
# Cable calculations
# ---------------------------------------------------------------------------

def calculate_loop_resistance(
    resistance_per_metre_ohm: float,
    cable_length_m: float,
    conductor_count: int = 2,
) -> float:
    """
    Calculate total loop resistance.

    R = resistance per metre × length × conductor count
    """

    if resistance_per_metre_ohm < 0:
        raise ValueError(
            "Resistance cannot be negative."
        )

    if cable_length_m < 0:
        raise ValueError(
            "Cable length cannot be negative."
        )

    if conductor_count < 1:
        raise ValueError(
            "Conductor count must be at least 1."
        )

    return (
        resistance_per_metre_ohm
        * cable_length_m
        * conductor_count
    )


def calculate_voltage_drop(
    current_ma: float,
    resistance_ohm: float,
) -> float:
    """
    Calculate voltage drop using Ohm's law.

    V = I × R
    """

    if current_ma < 0:
        raise ValueError(
            "Current cannot be negative."
        )

    if resistance_ohm < 0:
        raise ValueError(
            "Resistance cannot be negative."
        )

    current_amps = current_ma / 1000.0

    return current_amps * resistance_ohm


def calculate_end_voltage(
    supply_voltage_v: float,
    current_ma: float,
    resistance_ohm: float,
) -> float:
    """
    Calculate voltage at the end of the loop.
    """

    voltage_drop = calculate_voltage_drop(
        current_ma=current_ma,
        resistance_ohm=resistance_ohm,
    )

    return supply_voltage_v - voltage_drop


def calculate_voltage_result(
    supply_voltage_v: float,
    current_ma: float,
    resistance_ohm: float,
    minimum_voltage_v: float,
) -> VoltageDropResult:
    """
    Create a complete voltage-drop result.
    """

    voltage_drop = calculate_voltage_drop(
        current_ma=current_ma,
        resistance_ohm=resistance_ohm,
    )

    end_voltage = (
        supply_voltage_v - voltage_drop
    )

    return VoltageDropResult(
        supply_voltage_v=supply_voltage_v,

        current_ma=current_ma,

        cable_resistance_ohm=resistance_ohm,

        voltage_drop_v=voltage_drop,

        end_voltage_v=end_voltage,

        minimum_voltage_v=minimum_voltage_v,
    )


# ---------------------------------------------------------------------------
# Complete loop calculation
# ---------------------------------------------------------------------------

def calculate_complete_loop(
    devices: Iterable[Device],
    capacity_ma: float,
    supply_voltage_v: float,
    minimum_voltage_v: float = 0.0,
    cable_resistance_ohm: float | None = None,
):
    """
    Perform the complete ZP3 loop calculation.
    """

    load_result = calculate_loop_load(
        devices=devices,
        capacity_ma=capacity_ma,
    )

    standby_voltage_result = None
    alarm_voltage_result = None

    warnings: list[str] = []

    # ---------------------------------------------------------------
    # Voltage drop
    # ---------------------------------------------------------------

    if cable_resistance_ohm is not None:

        standby_voltage_result = calculate_voltage_result(
            supply_voltage_v=supply_voltage_v,
            current_ma=load_result.standby_load_ma,
            resistance_ohm=cable_resistance_ohm,
            minimum_voltage_v=minimum_voltage_v,
        )

        alarm_voltage_result = calculate_voltage_result(
            supply_voltage_v=supply_voltage_v,
            current_ma=load_result.alarm_load_ma,
            resistance_ohm=cable_resistance_ohm,
            minimum_voltage_v=minimum_voltage_v,
        )

        if not standby_voltage_result.voltage_ok:
            warnings.append(
                "Standby end voltage is below "
                "the minimum device voltage."
            )

        if not alarm_voltage_result.voltage_ok:
            warnings.append(
                "Alarm end voltage is below "
                "the minimum device voltage."
            )

    # ---------------------------------------------------------------
    # Load warnings
    # ---------------------------------------------------------------

    if load_result.standby_overload:
        warnings.append(
            "Standby current exceeds loop capacity."
        )

    if load_result.alarm_overload:
        warnings.append(
            "Alarm current exceeds loop capacity."
        )

    # ---------------------------------------------------------------
    # Result
    # ---------------------------------------------------------------

    return {
        "load": load_result,

        "standby_voltage":
            standby_voltage_result,

        "alarm_voltage":
            alarm_voltage_result,

        "warnings":
            warnings,
    }

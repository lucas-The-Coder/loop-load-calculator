from typing import List

from calculation_service import (
    calculate_cable_voltage_drop,
    calculate_loop_load,
)
from models import (
    Cable,
    Device,
    Loop,
    LoopConfiguration,
)
from schemas import (
    DeviceCreateSchema,
    LoopCalculationRequest,
    LoopConfigurationSchema,
    LoopCreateSchema,
    validate_loop_request,
)


# ---------------------------------------------------------------------------
# Application constants
# ---------------------------------------------------------------------------

DEFAULT_LOOP_CAPACITY_MA = 500.0
DEFAULT_SUPPLY_VOLTAGE_V = 24.0


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

def get_text(prompt: str, default: str = "") -> str:
    """Get text input from the user."""

    value = input(prompt).strip()

    if not value and default:
        return default

    return value


def get_int(
    prompt: str,
    default: int | None = None,
    minimum: int = 0,
) -> int:
    """Get a validated integer from the user."""

    while True:
        try:
            value = input(prompt).strip()

            if not value and default is not None:
                return default

            result = int(value)

            if result < minimum:
                print(
                    f"Please enter a value of {minimum} or greater."
                )
                continue

            return result

        except ValueError:
            print("Please enter a valid whole number.")


def get_float(
    prompt: str,
    default: float | None = None,
    minimum: float = 0.0,
) -> float:
    """Get a validated floating-point number."""

    while True:
        try:
            value = input(prompt).strip()

            if not value and default is not None:
                return default

            result = float(value)

            if result < minimum:
                print(
                    f"Please enter a value of {minimum} or greater."
                )
                continue

            return result

        except ValueError:
            print("Please enter a valid number.")


def get_yes_no(
    prompt: str,
    default: bool = False,
) -> bool:
    """Get a yes/no response."""

    default_text = "Y/n" if default else "y/N"

    while True:
        value = input(f"{prompt} [{default_text}]: ").strip().lower()

        if not value:
            return default

        if value in {"y", "yes"}:
            return True

        if value in {"n", "no"}:
            return False

        print("Please enter yes or no.")


# ---------------------------------------------------------------------------
# Device input
# ---------------------------------------------------------------------------

def collect_devices() -> List[DeviceCreateSchema]:
    """Collect device information from the user."""

    devices: List[DeviceCreateSchema] = []

    print("\n" + "-" * 70)
    print("DEVICE CONFIGURATION")
    print("-" * 70)
    print("Enter each device type installed on the loop.")
    print("Leave the device name blank when finished.\n")

    while True:
        name = input("Device name: ").strip()

        if not name:
            break

        quantity = get_int(
            "Quantity: ",
            minimum=1,
        )

        standby_current = get_float(
            "Standby current per device (mA): ",
            minimum=0.0,
        )

        alarm_current = get_float(
            "Alarm current per device (mA): ",
            minimum=0.0,
        )

        address = input(
            "Address/range (optional): "
        ).strip() or None

        notes = input(
            "Notes (optional): "
        ).strip()

        try:
            device = DeviceCreateSchema(
                name=name,
                quantity=quantity,
                standby_current_ma=standby_current,
                alarm_current_ma=alarm_current,
                address=address,
                notes=notes,
            )

            devices.append(device)

            print("Device added.\n")

        except ValueError as exc:
            print(f"Invalid device: {exc}\n")

    return devices


# ---------------------------------------------------------------------------
# Cable input
# ---------------------------------------------------------------------------

def collect_cable() -> Cable | None:
    """Collect cable information from the user."""

    print("\n" + "-" * 70)
    print("CABLE CONFIGURATION")
    print("-" * 70)

    use_cable = get_yes_no(
        "Do you want to calculate voltage drop?",
        default=False,
    )

    if not use_cable:
        return None

    cable_type = input(
        "Cable type/reference: "
    ).strip()

    length_m = get_float(
        "Cable length (m): ",
        minimum=0.0,
    )

    resistance_per_metre = get_float(
        "Resistance per conductor (ohm/m): ",
        minimum=0.0,
    )

    conductor_count = get_int(
        "Number of conductors in current path [2]: ",
        default=2,
        minimum=1,
    )

    return Cable(
        cable_type=cable_type,
        length_m=length_m,
        resistance_per_metre_ohm=resistance_per_metre,
        conductor_count=conductor_count,
    )


# ---------------------------------------------------------------------------
# Loop creation
# ---------------------------------------------------------------------------

def create_loop() -> Loop:
    """Collect information and create a loop."""

    print("\n" + "=" * 70)
    print("LOOP CONFIGURATION")
    print("=" * 70)

    loop_name = get_text(
        "Loop name [Loop 1]: ",
        default="Loop 1",
    )

    capacity_ma = get_float(
        f"Loop capacity (mA) "
        f"[{DEFAULT_LOOP_CAPACITY_MA}]: ",
        default=DEFAULT_LOOP_CAPACITY_MA,
        minimum=0.0001,
    )

    supply_voltage = get_float(
        f"Supply voltage (V) "
        f"[{DEFAULT_SUPPLY_VOLTAGE_V}]: ",
        default=DEFAULT_SUPPLY_VOLTAGE_V,
        minimum=0.0001,
    )

    minimum_voltage = get_float(
        "Minimum required device voltage (V) [0]: ",
        default=0.0,
        minimum=0.0,
    )

    devices = collect_devices()

    if not devices:
        raise ValueError(
            "At least one device must be entered."
        )

    cable = collect_cable()

    configuration_schema = LoopConfigurationSchema(
        name=loop_name,
        capacity_ma=capacity_ma,
        supply_voltage_v=supply_voltage,
        minimum_device_voltage_v=minimum_voltage,
        cable=cable,
    )

    loop_schema = LoopCreateSchema(
        configuration=configuration_schema,
        devices=devices,
    )

    request = LoopCalculationRequest(
        loop=loop_schema,
    )

    validate_loop_request(request)

    # Convert schema objects into domain models.
    model_devices = [
        Device(
            name=device.name,
            quantity=device.quantity,
            standby_current_ma=device.standby_current_ma,
            alarm_current_ma=device.alarm_current_ma,
            address=device.address,
            notes=device.notes,
        )
        for device in devices
    ]

    configuration = LoopConfiguration(
        name=configuration_schema.name,
        capacity_ma=configuration_schema.capacity_ma,
        supply_voltage_v=configuration_schema.supply_voltage_v,
        minimum_device_voltage_v=(
            configuration_schema.minimum_device_voltage_v
        ),
        cable=cable,
    )

    return Loop(
        configuration=configuration,
        devices=model_devices,
    )


# ---------------------------------------------------------------------------
# Calculation
# ---------------------------------------------------------------------------

def calculate(loop: Loop):
    """Perform the loop load calculation."""

    result = calculate_loop_load(
        devices=loop.devices,
        capacity_ma=loop.configuration.capacity_ma,
    )

    return result


# ---------------------------------------------------------------------------
# Result display
# ---------------------------------------------------------------------------

def print_device_breakdown(loop: Loop) -> None:
    """Display the individual device loads."""

    print("\n" + "-" * 70)
    print("DEVICE LOAD BREAKDOWN")
    print("-" * 70)

    print(
        f"{'Device':<30}"
        f"{'Qty':>6}"
        f"{'Standby':>16}"
        f"{'Alarm':>16}"
    )

    print("-" * 70)

    for device in loop.devices:
        print(
            f"{device.name:<30}"
            f"{device.quantity:>6}"
            f"{device.total_standby_current_ma:>13.2f} mA"
            f"{device.total_alarm_current_ma:>13.2f} mA"
        )


def print_load_results(loop: Loop, result) -> None:
    """Display current-load calculation results."""

    print("\n" + "=" * 70)
    print("LOOP LOAD RESULTS")
    print("=" * 70)

    print(f"Loop: {loop.configuration.name}")

    print("\nCURRENT LOAD")
    print("-" * 70)

    print(
        f"Loop capacity:       "
        f"{result.capacity_ma:.2f} mA"
    )

    print(
        f"Standby load:        "
        f"{result.standby_load_ma:.2f} mA"
    )

    print(
        f"Standby utilisation: "
        f"{result.standby_percentage:.2f}%"
    )

    print(
        f"Standby remaining:   "
        f"{result.standby_remaining_ma:.2f} mA"
    )

    print()

    print(
        f"Alarm load:          "
        f"{result.alarm_load_ma:.2f} mA"
    )

    print(
        f"Alarm utilisation:   "
        f"{result.alarm_percentage:.2f}%"
    )

    print(
        f"Alarm remaining:     "
        f"{result.alarm_remaining_ma:.2f} mA"
    )

    print("\nCAPACITY STATUS")
    print("-" * 70)

    if result.standby_overload:
        print("❌ Standby load EXCEEDS loop capacity.")
    else:
        print("✓ Standby load is within loop capacity.")

    if result.alarm_overload:
        print("❌ Alarm load EXCEEDS loop capacity.")
    else:
        print("✓ Alarm load is within loop capacity.")

    if result.is_within_capacity:
        print("\n✓ CURRENT LOAD CHECK: PASS")
    else:
        print("\n❌ CURRENT LOAD CHECK: FAIL")


def print_voltage_results(loop: Loop) -> None:
    """Calculate and display voltage-drop results."""

    cable = loop.configuration.cable

    if cable is None:
        return

    print("\n" + "=" * 70)
    print("VOLTAGE DROP")
    print("=" * 70)

    resistance = cable.total_resistance_ohm

    print(
        f"Cable type:          "
        f"{cable.cable_type or 'Not specified'}"
    )

    print(
        f"Cable length:        "
        f"{cable.length_m:.2f} m"
    )

    print(
        f"Cable resistance:    "
        f"{resistance:.4f} ohm"
    )

    result = calculate_loop_load(
        devices=loop.devices,
        capacity_ma=loop.configuration.capacity_ma,
    )

    # Standby voltage
    standby_drop = calculate_cable_voltage_drop(
        current_ma=result.standby_load_ma,
        resistance_per_metre_ohm=(
            cable.resistance_per_metre_ohm
        ),
        cable_length_m=cable.length_m,
        conductor_count=cable.conductor_count,
    )

    standby_voltage = (
        loop.configuration.supply_voltage_v
        - standby_drop
    )

    print("\nSTANDBY")
    print("-" * 70)

    print(
        f"Current:             "
        f"{result.standby_load_ma:.2f} mA"
    )

    print(
        f"Voltage drop:        "
        f"{standby_drop:.3f} V"
    )

    print(
        f"End voltage:         "
        f"{standby_voltage:.3f} V"
    )

    # Alarm voltage
    alarm_drop = calculate_cable_voltage_drop(
        current_ma=result.alarm_load_ma,
        resistance_per_metre_ohm=(
            cable.resistance_per_metre_ohm
        ),
        cable_length_m=cable.length_m,
        conductor_count=cable.conductor_count,
    )

    alarm_voltage = (
        loop.configuration.supply_voltage_v
        - alarm_drop
    )

    print("\nALARM")
    print("-" * 70)

    print(
        f"Current:             "
        f"{result.alarm_load_ma:.2f} mA"
    )

    print(
        f"Voltage drop:        "
        f"{alarm_drop:.3f} V"
    )

    print(
        f"End voltage:         "
        f"{alarm_voltage:.3f} V"
    )

    minimum_voltage = (
        loop.configuration.minimum_device_voltage_v
    )

    if minimum_voltage > 0:
        print(
            f"\nMinimum required:    "
            f"{minimum_voltage:.3f} V"
        )

        standby_ok = standby_voltage >= minimum_voltage
        alarm_ok = alarm_voltage >= minimum_voltage

        print(
            "Standby voltage:     "
            f"{'PASS' if standby_ok else 'FAIL'}"
        )

        print(
            "Alarm voltage:       "
            f"{'PASS' if alarm_ok else 'FAIL'}"
        )


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

def run_application() -> None:
    """Run the ZP3 loop load calculator."""

    print("\n" + "=" * 70)
    print("ZP3 LOOP LOAD CALCULATOR")
    print("=" * 70)

    print(
        "\nEnter the electrical data from the applicable "
        "panel/module and device documentation."
    )

    try:
        loop = create_loop()

        print_device_breakdown(loop)

        result = calculate(loop)

        print_load_results(
            loop=loop,
            result=result,
        )

        print_voltage_results(loop)

    except ValueError as exc:
        print(f"\n❌ Input error: {exc}")

    except KeyboardInterrupt:
        print("\n\nCalculation cancelled.")

    print("\n" + "=" * 70)
    print("CALCULATION COMPLETE")
    print("=" * 70)


def main() -> None:
    """Program entry point."""

    run_application()


if __name__ == "__main__":
    main()

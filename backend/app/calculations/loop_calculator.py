from dataclasses import dataclass
from typing import List


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Set this to the maximum loop current for your specific ZP3 configuration.
LOOP_CAPACITY_MA = 500.0


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Device:
    name: str
    quantity: int
    standby_ma: float
    alarm_ma: float

    @property
    def standby_total_ma(self) -> float:
        return self.quantity * self.standby_ma

    @property
    def alarm_total_ma(self) -> float:
        return self.quantity * self.alarm_ma


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------

class LoopCalculator:
    def __init__(self, capacity_ma: float):
        if capacity_ma <= 0:
            raise ValueError("Loop capacity must be greater than zero.")

        self.capacity_ma = capacity_ma
        self.devices: List[Device] = []

    def add_device(
        self,
        name: str,
        quantity: int,
        standby_ma: float,
        alarm_ma: float,
    ) -> None:
        if quantity < 1:
            raise ValueError("Quantity must be at least 1.")

        if standby_ma < 0 or alarm_ma < 0:
            raise ValueError("Current values cannot be negative.")

        self.devices.append(
            Device(
                name=name,
                quantity=quantity,
                standby_ma=standby_ma,
                alarm_ma=alarm_ma,
            )
        )

    @property
    def total_standby_ma(self) -> float:
        return sum(device.standby_total_ma for device in self.devices)

    @property
    def total_alarm_ma(self) -> float:
        return sum(device.alarm_total_ma for device in self.devices)

    @property
    def standby_percentage(self) -> float:
        return (self.total_standby_ma / self.capacity_ma) * 100

    @property
    def alarm_percentage(self) -> float:
        return (self.total_alarm_ma / self.capacity_ma) * 100

    @property
    def standby_remaining_ma(self) -> float:
        return self.capacity_ma - self.total_standby_ma

    @property
    def alarm_remaining_ma(self) -> float:
        return self.capacity_ma - self.total_alarm_ma

    def print_report(self) -> None:
        print("\n" + "=" * 70)
        print("ZP3 LOOP LOAD CALCULATOR")
        print("=" * 70)

        print(
            f"{'Device':<30}"
            f"{'Qty':>6}"
            f"{'Standby':>14}"
            f"{'Alarm':>14}"
        )
        print("-" * 70)

        for device in self.devices:
            print(
                f"{device.name:<30}"
                f"{device.quantity:>6}"
                f"{device.standby_total_ma:>11.2f} mA"
                f"{device.alarm_total_ma:>11.2f} mA"
            )

        print("-" * 70)

        print(
            f"{'TOTAL':<30}"
            f"{'':>6}"
            f"{self.total_standby_ma:>11.2f} mA"
            f"{self.total_alarm_ma:>11.2f} mA"
        )

        print("\nLOOP CAPACITY")
        print("-" * 70)
        print(f"Configured capacity : {self.capacity_ma:.2f} mA")

        print("\nSTANDBY LOAD")
        print("-" * 70)
        print(f"Load                : {self.total_standby_ma:.2f} mA")
        print(f"Utilisation         : {self.standby_percentage:.2f}%")
        print(f"Remaining capacity  : {self.standby_remaining_ma:.2f} mA")

        print("\nALARM LOAD")
        print("-" * 70)
        print(f"Load                : {self.total_alarm_ma:.2f} mA")
        print(f"Utilisation         : {self.alarm_percentage:.2f}%")
        print(f"Remaining capacity  : {self.alarm_remaining_ma:.2f} mA")

        print("\nSTATUS")
        print("-" * 70)

        if self.total_standby_ma > self.capacity_ma:
            print("WARNING: Standby load EXCEEDS loop capacity!")
        else:
            print("Standby load: OK")

        if self.total_alarm_ma > self.capacity_ma:
            print("WARNING: Alarm load EXCEEDS loop capacity!")
        else:
            print("Alarm load: OK")

        print("=" * 70)


# ---------------------------------------------------------------------------
# Interactive input
# ---------------------------------------------------------------------------

def get_float(prompt: str) -> float:
    while True:
        try:
            value = float(input(prompt))

            if value < 0:
                print("Please enter a value of 0 or greater.")
                continue

            return value

        except ValueError:
            print("Please enter a valid number.")


def get_int(prompt: str) -> int:
    while True:
        try:
            value = int(input(prompt))

            if value < 1:
                print("Please enter a quantity of at least 1.")
                continue

            return value

        except ValueError:
            print("Please enter a whole number.")


def main() -> None:
    print("=" * 70)
    print("ZP3 LOOP LOAD CALCULATOR")
    print("=" * 70)

    capacity = get_float(
        f"\nLoop capacity in mA [{LOOP_CAPACITY_MA}]: "
    )

    if capacity == 0:
        capacity = LOOP_CAPACITY_MA

    calculator = LoopCalculator(capacity)

    print("\nEnter the devices installed on the loop.")
    print("Leave the device name blank when finished.\n")

    while True:
        name = input("Device name: ").strip()

        if not name:
            break

        quantity = get_int("Quantity: ")
        standby_ma = get_float("Standby current (mA): ")
        alarm_ma = get_float("Alarm current (mA): ")

        calculator.add_device(
            name=name,
            quantity=quantity,
            standby_ma=standby_ma,
            alarm_ma=alarm_ma,
        )

        print("Device added.\n")

    if not calculator.devices:
        print("\nNo devices were entered.")
        return

    calculator.print_report()


# ---------------------------------------------------------------------------
# Program entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
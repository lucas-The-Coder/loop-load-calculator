from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from .models import Device

from .schemas import (
    LoopCalculationRequest,
    CalculationResultSchema,
)

from .services.calculation_service import (
    calculate_complete_loop,
)


# ============================================================================
# Application
# ============================================================================

app = FastAPI(
    title="ZP3 Loop Load Calculator",
    description="ZP3 loop load calculation API",
    version="1.0.0",
)


# ============================================================================
# Paths
# ============================================================================

# Project:
#
# loop-load-calculator/
#
#     index.html
#     vercel.json
#
#     backend/
#         app/
#             main.py
#
# parents[0] = app
# parents[1] = backend
# parents[2] = project root

PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]

INDEX_FILE = PROJECT_ROOT / "index.html"


# ============================================================================
# Frontend
# ============================================================================

@app.get(
    "/",
    include_in_schema=False,
)
async def frontend():
    """
    Serve index.html from the project root.
    """

    if not INDEX_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="index.html not found in project root.",
        )

    return FileResponse(
        INDEX_FILE,
        media_type="text/html",
    )


# ============================================================================
# Health check
# ============================================================================

@app.get("/api/health")
async def health_check():
    """
    API health check.
    """

    return {
        "status": "ok",
        "application": "ZP3 Loop Load Calculator",
        "version": "1.0.0",
    }


# ============================================================================
# Calculation
# ============================================================================

@app.post(
    "/api/calculate",
    response_model=CalculationResultSchema,
)
async def calculate_loop(
    request: LoopCalculationRequest,
):
    """
    Calculate loop load and optional voltage drop.
    """

    try:

        # ------------------------------------------------------------------
        # Configuration
        # ------------------------------------------------------------------

        loop_config = (
            request
            .loop
            .configuration
        )


        # ------------------------------------------------------------------
        # Devices
        # ------------------------------------------------------------------

        devices = []

        for device in request.loop.devices:

            devices.append(
                Device(
                    name=device.name,
                    quantity=device.quantity,
                    standby_current_ma=(
                        device.standby_current_ma
                    ),
                    alarm_current_ma=(
                        device.alarm_current_ma
                    ),
                    address=device.address,
                    notes=device.notes,
                )
            )


        # ------------------------------------------------------------------
        # Cable
        # ------------------------------------------------------------------

        cable_resistance_ohm = None

        cable = loop_config.cable

        if cable is not None:

            cable_resistance_ohm = (
                cable.resistance_per_metre_ohm
                * cable.length_m
                * cable.conductor_count
            )


        # ------------------------------------------------------------------
        # Calculation
        # ------------------------------------------------------------------

        result = calculate_complete_loop(
            devices=devices,

            capacity_ma=(
                loop_config.capacity_ma
            ),

            supply_voltage_v=(
                loop_config.supply_voltage_v
            ),

            minimum_voltage_v=(
                loop_config
                .minimum_device_voltage_v
            ),

            cable_resistance_ohm=(
                cable_resistance_ohm
            ),
        )


        # ------------------------------------------------------------------
        # Load
        # ------------------------------------------------------------------

        load = result["load"]


        # ------------------------------------------------------------------
        # Standby voltage
        # ------------------------------------------------------------------

        standby_voltage = None

        voltage = result.get(
            "standby_voltage"
        )

        if voltage is not None:

            standby_voltage = {
                "supply_voltage_v":
                    voltage.supply_voltage_v,

                "current_ma":
                    voltage.current_ma,

                "cable_resistance_ohm":
                    voltage.cable_resistance_ohm,

                "voltage_drop_v":
                    voltage.voltage_drop_v,

                "end_voltage_v":
                    voltage.end_voltage_v,

                "minimum_voltage_v":
                    voltage.minimum_voltage_v,

                "voltage_margin_v":
                    voltage.voltage_margin_v,

                "voltage_ok":
                    voltage.voltage_ok,
            }


        # ------------------------------------------------------------------
        # Alarm voltage
        # ------------------------------------------------------------------

        alarm_voltage = None

        voltage = result.get(
            "alarm_voltage"
        )

        if voltage is not None:

            alarm_voltage = {
                "supply_voltage_v":
                    voltage.supply_voltage_v,

                "current_ma":
                    voltage.current_ma,

                "cable_resistance_ohm":
                    voltage.cable_resistance_ohm,

                "voltage_drop_v":
                    voltage.voltage_drop_v,

                "end_voltage_v":
                    voltage.end_voltage_v,

                "minimum_voltage_v":
                    voltage.minimum_voltage_v,

                "voltage_margin_v":
                    voltage.voltage_margin_v,

                "voltage_ok":
                    voltage.voltage_ok,
            }


        # ------------------------------------------------------------------
        # Overall result
        # ------------------------------------------------------------------

        passed = bool(
            load.within_capacity
        )


        if standby_voltage is not None:

            passed = (
                passed
                and bool(
                    standby_voltage[
                        "voltage_ok"
                    ]
                )
            )


        if alarm_voltage is not None:

            passed = (
                passed
                and bool(
                    alarm_voltage[
                        "voltage_ok"
                    ]
                )
            )


        # ------------------------------------------------------------------
        # Response
        # ------------------------------------------------------------------

        return CalculationResultSchema(

            loop_name=(
                loop_config.name
            ),

            load={
                "capacity_ma":
                    load.capacity_ma,

                "standby_load_ma":
                    load.standby_load_ma,

                "alarm_load_ma":
                    load.alarm_load_ma,

                "standby_remaining_ma":
                    load.standby_remaining_ma,

                "alarm_remaining_ma":
                    load.alarm_remaining_ma,

                "standby_percentage":
                    load.standby_percentage,

                "alarm_percentage":
                    load.alarm_percentage,

                "standby_overload":
                    load.standby_overload,

                "alarm_overload":
                    load.alarm_overload,

                "within_capacity":
                    load.within_capacity,
            },

            standby_voltage=(
                standby_voltage
            ),

            alarm_voltage=(
                alarm_voltage
            ),

            warnings=result.get(
                "warnings",
                [],
            ),

            passed=passed,
        )


    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Calculation error: {exc}",
        ) from exc

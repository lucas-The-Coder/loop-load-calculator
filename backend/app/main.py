from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from calculation_service import (
    calculate_complete_loop,
    calculate_loop_resistance,
)
from models import Cable, Device
from schemas import (
    CalculationResultSchema,
    LoopCalculationRequest,
)


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="ZP3 Loop Load Calculator",
    description="Mobile-first ZP3 loop load calculation API",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)


@app.get("/", include_in_schema=False)
async def frontend():
    """Serve the mobile web application."""

    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health_check():
    """Simple backend health check."""

    return {
        "status": "ok",
        "application": "ZP3 Loop Load Calculator",
    }


@app.post(
    "/api/calculate",
    response_model=CalculationResultSchema,
)
async def calculate(
    request: LoopCalculationRequest,
):
    """
    Calculate the electrical load of a ZP3 loop.
    """

    try:

        loop_config = request.loop.configuration

        # ---------------------------------------------------------------
        # Convert schemas to domain models
        # ---------------------------------------------------------------

        devices = [
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
            for device in request.loop.devices
        ]

        # ---------------------------------------------------------------
        # Cable
        # ---------------------------------------------------------------

        cable_resistance = None

        cable_schema = loop_config.cable

        if cable_schema is not None:

            cable = Cable(
                cable_type=cable_schema.cable_type,
                length_m=cable_schema.length_m,
                resistance_per_metre_ohm=(
                    cable_schema
                    .resistance_per_metre_ohm
                ),
                conductor_count=(
                    cable_schema.conductor_count
                ),
            )

            cable_resistance = (
                cable.total_resistance_ohm
            )

        # ---------------------------------------------------------------
        # Calculate
        # ---------------------------------------------------------------

        result = calculate_complete_loop(
            devices=devices,
            capacity_ma=loop_config.capacity_ma,
            supply_voltage_v=(
                loop_config.supply_voltage_v
            ),
            minimum_voltage_v=(
                loop_config.minimum_device_voltage_v
            ),
            cable_resistance_ohm=cable_resistance,
        )

        load = result["load"]

        # ---------------------------------------------------------------
        # Convert calculation results to API schema
        # ---------------------------------------------------------------

        standby_voltage = None

        if result["standby_voltage"] is not None:

            voltage = result["standby_voltage"]

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

        alarm_voltage = None

        if result["alarm_voltage"] is not None:

            voltage = result["alarm_voltage"]

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

        return CalculationResultSchema(
            loop_name=loop_config.name,

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

            standby_voltage=standby_voltage,

            alarm_voltage=alarm_voltage,

            warnings=result["warnings"],

            passed=(
                load.within_capacity
                and (
                    standby_voltage is None
                    or standby_voltage["voltage_ok"]
                )
                and (
                    alarm_voltage is None
                    or alarm_voltage["voltage_ok"]
                )
            ),
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail="An unexpected calculation error occurred.",
        ) from exc


# ---------------------------------------------------------------------------
# Development server
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

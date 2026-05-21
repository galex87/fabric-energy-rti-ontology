#!/usr/bin/env python3
"""Live wind/solar/grid telemetry simulator for Microsoft Fabric RTI demos."""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from datetime import datetime, timezone

SITE_IDS = ("north-farm", "south-farm", "coastal-farm")


def classify_alert(renewable_ratio: float, grid_demand_mw: float, co2_intensity_g_kwh: float) -> str:
    if renewable_ratio < 0.25 and grid_demand_mw > 160:
        return "critical"
    if renewable_ratio < 0.40 or co2_intensity_g_kwh > 380:
        return "warning"
    return "normal"


def _solar_factor(hour_utc: int) -> float:
    if hour_utc < 6 or hour_utc > 19:
        return 0.0
    daylight_span = 19 - 6
    x = (hour_utc - 6) / daylight_span
    return max(0.0, math.sin(math.pi * x))


def generate_event(rng: random.Random, sequence: int) -> dict[str, float | int | str]:
    now = datetime.now(timezone.utc)
    hour = now.hour

    wind_mw = max(0.0, min(125.0, rng.gauss(68, 18)))
    solar_mw = max(0.0, min(90.0, rng.gauss(65 * _solar_factor(hour), 10)))
    grid_demand_mw = max(80.0, min(220.0, rng.gauss(145, 28)))
    renewable_ratio = min(1.0, (wind_mw + solar_mw) / grid_demand_mw)
    co2_intensity = max(140.0, 460.0 - (renewable_ratio * 260.0) + rng.gauss(0, 8))

    event = {
        "event_id": sequence,
        "timestamp_utc": now.isoformat(),
        "site_id": rng.choice(SITE_IDS),
        "wind_mw": round(wind_mw, 2),
        "solar_mw": round(solar_mw, 2),
        "grid_demand_mw": round(grid_demand_mw, 2),
        "renewable_ratio": round(renewable_ratio, 4),
        "co2_intensity_g_kwh": round(co2_intensity, 2),
    }
    event["alert_level"] = classify_alert(
        renewable_ratio=event["renewable_ratio"],
        grid_demand_mw=event["grid_demand_mw"],
        co2_intensity_g_kwh=event["co2_intensity_g_kwh"],
    )
    return event


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval-seconds", type=float, default=2.0)
    parser.add_argument("--events", type=int, default=0, help="0 means run forever")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rng = random.Random(args.seed)

    sequence = 1
    while True:
        event = generate_event(rng, sequence)
        if args.pretty:
            print(json.dumps(event, indent=2), flush=True)
        else:
            print(json.dumps(event, separators=(",", ":")), flush=True)

        sequence += 1
        if args.events > 0 and sequence > args.events:
            break
        time.sleep(max(0.0, args.interval_seconds))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

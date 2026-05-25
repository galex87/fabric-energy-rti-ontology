# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "bd9c69ce-ee2b-45a9-854d-13696f476a96",
# META       "default_lakehouse_name": "AegeanPowerLH",
# META       "default_lakehouse_workspace_id": "21dbf808-03bb-44d9-a8f4-ac6166b1ce08",
# META       "known_lakehouses": [
# META         {
# META           "id": "bd9c69ce-ee2b-45a9-854d-13696f476a96"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# # Aegean Power S.A. — Real-Time Telemetry Simulator
# **Microsoft Fabric · Real-Time Intelligence + Fabric IQ Demo**
#
# Generates physics-based energy telemetry for a fictional Greek energy company
# operating wind farms, solar parks, gas plants, and LNG logistics across Greece.
#
# | Stream | Assets | Default cadence |
# |--------|--------|-----------------|
# | WindTurbineTelemetry | 20 turbines (Thrace, Tinos, Naxos) | 2 s |
# | SolarInverterTelemetry | 15 inverters (Thessaly, Crete) | 6 s |
# | GridTelemetry | 6 grid zones (Mainland + 5 islands) | 2 s |
# | VesselPositions | 3 vessels (2 LNG + 1 service) | 10 s |
# | EmissionsStream | 2 gas plants (Lavrio, Megalopoli) | 30 s |
#
# Sends to Fabric Eventstream Custom Endpoint via `azure-eventhub`.

# MARKDOWN ********************

# ## Install dependencies

# CELL ********************

# >>> Install the Azure Event Hubs SDK (used to send events to the
#     Fabric Eventstream Custom Endpoint). Commented out after first run.
%pip install azure-eventhub --quiet

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Delete every file in Files/control (clear forgotten control files)
import notebookutils as nu

CTRL = "Files/control"

try:
    items = nu.fs.ls(CTRL)
except Exception:
    items = []
    nu.fs.mkdirs(CTRL)

deleted = 0
for it in items:
    nu.fs.rm(it.path, recurse=True)
    print(f"removed {it.name}")
    deleted += 1

print(f"\nDeleted {deleted} item(s) from {CTRL}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Parameters
# Edit these before running. The first parameter cell controls everything.

# CELL ********************

# >>> One-stop control panel for the entire demo. Every knob lives here:
#     destination, pacing, which assets fail, how often, how badly.
# ============================================================
#  SIMULATOR PARAMETERS
# ============================================================

# -- Eventstream destination ---------------------------------
EVENTHUB_CONNECTION_STRING = "REPLACE_ME_WITH_EVENTSTREAM_CUSTOM_ENDPOINT_CONNECTION_STRING"  # see README: AegeanPowerStream2 → Source → Custom App → Sample code → Connection string-primary key

# -- Master clock --------------------------------------------
INTERVAL_SECONDS = 2          # base tick rate (everything is a multiple of this)
MAX_CYCLES       = 0          # 0 = run forever (Interrupt cell to stop)

# -- Per-stream cadence (in number of base ticks) ------------
WIND_EVERY_N      = 1         # -> every 2 s
SOLAR_EVERY_N     = 3         # -> every 6 s
GRID_EVERY_N      = 1         # -> every 2 s
VESSEL_EVERY_N    = 1         # -> every 2 s
EMISSIONS_EVERY_N = 15        # -> every 30 s

# -- Solar / time --------------------------------------------
FORCE_DAYTIME = True          # pin solar at noon (useful for evening demos)

# -- Scripted incident (the headline story) ------------------
ENABLE_SCRIPTED_INCIDENT = True
SCRIPTED_INCIDENT_TURBINE = "WT-NAX-07"   # progressive bearing degradation

# -- Random anomaly injection (background noise of faults) ---
ENABLE_ANOMALIES = True

ANOMALY_WIND_TURBINES   = 2   # # of random turbines (excl. scripted) with vibration spikes
ANOMALY_SOLAR_INVERTERS = 1   # # of random inverters with efficiency drops
ANOMALY_GAS_PLANTS      = 0   # # of random gas plants with emissions spikes

ANOMALY_PROBABILITY  = 0.08   # per-cycle probability that an affected asset misbehaves
ANOMALY_SEVERITY_MIN = 2.0    # multiplier on baseline (min)
ANOMALY_SEVERITY_MAX = 4.0    # multiplier on baseline (max)

# -- Console output ------------------------------------------
PRINT_EVERY_N_CYCLES = 5      # print summary every N base ticks (0 = quiet)

# -- Reproducibility -----------------------------------------
RANDOM_SEED = None            # set to e.g. 42 for deterministic anomaly assets

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Asset registry
# Turbines, inverters, grids, vessels, gas plants — embedded for portability.

# CELL ********************

# >>> The complete fleet definition for Aegean Power S.A.
#     20 wind turbines (Thrace, Tinos, Naxos), 15 solar inverters
#     (Thessaly, Crete), 6 grid zones (mainland + 5 islands),
#     3 vessels (2 LNG carriers + 1 service boat), 2 gas plants.
#     All coordinates are real Greek locations.

import time, math, random, json
from datetime import datetime, timezone
from azure.eventhub import EventHubProducerClient, EventData

# Guard: allow this cell to run independently of the parameters cell.
if 'RANDOM_SEED' in globals() and RANDOM_SEED is not None:
    random.seed(RANDOM_SEED)

# -- Wind turbines (20) --------------------------------------
WIND_TURBINES = [
    {"id":"WT-THR-01","plant":"PP-THR-01","region":"thrace","cap":4.2,"cut_in":3.0,"rated":12.0,"cut_out":25.0,"lat":40.852,"lon":25.865},
    {"id":"WT-THR-02","plant":"PP-THR-01","region":"thrace","cap":4.2,"cut_in":3.0,"rated":12.0,"cut_out":25.0,"lat":40.854,"lon":25.868},
    {"id":"WT-THR-03","plant":"PP-THR-01","region":"thrace","cap":4.2,"cut_in":3.0,"rated":12.0,"cut_out":25.0,"lat":40.851,"lon":25.872},
    {"id":"WT-THR-04","plant":"PP-THR-01","region":"thrace","cap":4.2,"cut_in":3.0,"rated":12.0,"cut_out":25.0,"lat":40.848,"lon":25.875},
    {"id":"WT-THR-05","plant":"PP-THR-01","region":"thrace","cap":4.2,"cut_in":3.0,"rated":12.0,"cut_out":25.0,"lat":40.846,"lon":25.877},
    {"id":"WT-THR-06","plant":"PP-THR-01","region":"thrace","cap":4.2,"cut_in":3.0,"rated":12.0,"cut_out":25.0,"lat":40.850,"lon":25.880},
    {"id":"WT-THR-07","plant":"PP-THR-01","region":"thrace","cap":4.2,"cut_in":3.0,"rated":12.0,"cut_out":25.0,"lat":40.853,"lon":25.883},
    {"id":"WT-THR-08","plant":"PP-THR-01","region":"thrace","cap":4.2,"cut_in":3.0,"rated":12.0,"cut_out":25.0,"lat":40.855,"lon":25.886},
    {"id":"WT-TIN-01","plant":"PP-TIN-01","region":"tinos","cap":3.4,"cut_in":3.0,"rated":11.5,"cut_out":25.0,"lat":37.610,"lon":25.145},
    {"id":"WT-TIN-02","plant":"PP-TIN-01","region":"tinos","cap":3.4,"cut_in":3.0,"rated":11.5,"cut_out":25.0,"lat":37.613,"lon":25.148},
    {"id":"WT-TIN-03","plant":"PP-TIN-01","region":"tinos","cap":3.4,"cut_in":3.0,"rated":11.5,"cut_out":25.0,"lat":37.616,"lon":25.152},
    {"id":"WT-TIN-04","plant":"PP-TIN-01","region":"tinos","cap":3.4,"cut_in":3.0,"rated":11.5,"cut_out":25.0,"lat":37.600,"lon":25.162},
    {"id":"WT-TIN-05","plant":"PP-TIN-01","region":"tinos","cap":3.4,"cut_in":3.0,"rated":11.5,"cut_out":25.0,"lat":37.603,"lon":25.165},
    {"id":"WT-NAX-01","plant":"PP-NAX-01","region":"naxos","cap":4.2,"cut_in":2.5,"rated":12.0,"cut_out":28.0,"lat":37.080,"lon":25.460},
    {"id":"WT-NAX-02","plant":"PP-NAX-01","region":"naxos","cap":4.2,"cut_in":2.5,"rated":12.0,"cut_out":28.0,"lat":37.078,"lon":25.463},
    {"id":"WT-NAX-03","plant":"PP-NAX-01","region":"naxos","cap":4.2,"cut_in":2.5,"rated":12.0,"cut_out":28.0,"lat":37.076,"lon":25.466},
    {"id":"WT-NAX-04","plant":"PP-NAX-01","region":"naxos","cap":4.2,"cut_in":2.5,"rated":12.0,"cut_out":28.0,"lat":37.065,"lon":25.478},
    {"id":"WT-NAX-05","plant":"PP-NAX-01","region":"naxos","cap":4.2,"cut_in":2.5,"rated":12.0,"cut_out":28.0,"lat":37.063,"lon":25.481},
    {"id":"WT-NAX-06","plant":"PP-NAX-01","region":"naxos","cap":4.2,"cut_in":2.5,"rated":12.0,"cut_out":28.0,"lat":37.060,"lon":25.484},
    {"id":"WT-NAX-07","plant":"PP-NAX-01","region":"naxos","cap":4.2,"cut_in":2.5,"rated":12.0,"cut_out":28.0,"lat":37.070,"lon":25.492},
]

# -- Solar inverters (15) ------------------------------------
SOLAR_INVERTERS = [
    {"id":"SI-THE-01","plant":"PP-THE-01","region":"thessaly","cap_kw":10000,"lat":39.652,"lon":22.395},
    {"id":"SI-THE-02","plant":"PP-THE-01","region":"thessaly","cap_kw":10000,"lat":39.653,"lon":22.398},
    {"id":"SI-THE-03","plant":"PP-THE-01","region":"thessaly","cap_kw":10000,"lat":39.654,"lon":22.401},
    {"id":"SI-THE-04","plant":"PP-THE-01","region":"thessaly","cap_kw":10000,"lat":39.648,"lon":22.405},
    {"id":"SI-THE-05","plant":"PP-THE-01","region":"thessaly","cap_kw":10000,"lat":39.649,"lon":22.408},
    {"id":"SI-THE-06","plant":"PP-THE-01","region":"thessaly","cap_kw":10000,"lat":39.650,"lon":22.411},
    {"id":"SI-THE-07","plant":"PP-THE-01","region":"thessaly","cap_kw":10000,"lat":39.646,"lon":22.415},
    {"id":"SI-THE-08","plant":"PP-THE-01","region":"thessaly","cap_kw":10000,"lat":39.647,"lon":22.418},
    {"id":"SI-CRE-01","plant":"PP-CRE-01","region":"crete","cap_kw":8570,"lat":35.332,"lon":25.135},
    {"id":"SI-CRE-02","plant":"PP-CRE-01","region":"crete","cap_kw":8570,"lat":35.333,"lon":25.138},
    {"id":"SI-CRE-03","plant":"PP-CRE-01","region":"crete","cap_kw":8570,"lat":35.334,"lon":25.141},
    {"id":"SI-CRE-04","plant":"PP-CRE-01","region":"crete","cap_kw":8570,"lat":35.328,"lon":25.145},
    {"id":"SI-CRE-05","plant":"PP-CRE-01","region":"crete","cap_kw":8570,"lat":35.329,"lon":25.148},
    {"id":"SI-CRE-06","plant":"PP-CRE-01","region":"crete","cap_kw":8570,"lat":35.330,"lon":25.151},
    {"id":"SI-CRE-07","plant":"PP-CRE-01","region":"crete","cap_kw":8570,"lat":35.331,"lon":25.154},
]

# -- Gas plants (2) ------------------------------------------
GAS_PLANTS = [
    {"id":"PP-LAV-01","name":"Lavrio Gas CCGT","cap_mw":400,"ef":0.35,"ets_daily":2100,"lat":37.720,"lon":24.050},
    {"id":"PP-MEG-01","name":"Megalopoli Gas Unit","cap_mw":200,"ef":0.35,"ets_daily":1100,"lat":37.400,"lon":22.140},
]

# -- Grids (6) -----------------------------------------------
ISLAND_GRIDS = [
    {"id":"GR-MAIN","name":"Mainland Grid","base_load":5500,"inertia":50000},
    {"id":"GR-CRE","name":"Crete Grid","base_load":550,"inertia":3000},
    {"id":"GR-NAX","name":"Naxos Grid","base_load":22,"inertia":200},
    {"id":"GR-TIN","name":"Tinos Grid","base_load":15,"inertia":150},
    {"id":"GR-MYK","name":"Mykonos Grid","base_load":40,"inertia":300},
    {"id":"GR-CYC","name":"Cyclades Hub","base_load":30,"inertia":250},
]

# -- Vessels (3) - Real Aegean shipping corridors --
# Hellas Spirit: Kasos Strait -> Cyclades east -> Kafireas Strait -> Saronic -> Revithoussa
# Aegean Breeze: Antikythira Strait -> Cape Maleas -> Argolic Gulf -> Saronic -> Revithoussa
# Poseidon: parked at Piraeus; dispatched via Cyclades south corridor when needed
VESSELS = [
    {"id":"VE-LNG-01","name":"Hellas Spirit","type":"LNG Carrier","cargo":"Loaded","speed":18.0,"destination":"Revithoussa LNG Terminal",
     "route":[
        (34.50, 27.80),
        (34.95, 27.20),
        (35.40, 26.80),
        (35.85, 26.40),
        (36.30, 26.05),
        (36.70, 25.65),
        (37.05, 25.30),
        (37.40, 25.00),
        (37.85, 24.55),
        (38.05, 24.10),
        (37.95, 23.80),
        (37.92, 23.55),
        (37.96, 23.38)
     ],
     "start_pct":0.10},
    {"id":"VE-LNG-02","name":"Aegean Breeze","type":"LNG Carrier","cargo":"Loaded","speed":17.0,"destination":"Revithoussa LNG Terminal",
     "route":[
        (35.20, 21.50),
        (35.50, 22.00),
        (35.85, 22.55),
        (36.20, 22.85),
        (36.55, 22.85),
        (36.85, 22.95),
        (37.10, 23.05),
        (37.35, 23.15),
        (37.55, 23.25),
        (37.75, 23.32),
        (37.90, 23.36),
        (37.96, 23.38)
     ],
     "start_pct":0.25},
    {"id":"VE-SVC-01","name":"Poseidon Service","type":"Crew Transfer Vessel","cargo":"Crew + spare parts","speed":22.0,"destination":"Piraeus Port (standby)",
     "route":[(37.94, 23.62), (37.94, 23.62)],
     "start_pct":0.0},
]

print(f"Loaded: {len(WIND_TURBINES)} turbines, {len(SOLAR_INVERTERS)} inverters, {len(GAS_PLANTS)} gas plants, {len(ISLAND_GRIDS)} grids, {len(VESSELS)} vessels")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Physics models
# Wind (Ornstein-Uhlenbeck), solar (Kasten-Young clear-sky), vessel navigation (haversine).

# CELL ********************

# >>> Realistic physics for each asset type.
#     - WindModel: regional wind speed via mean-reverting random walk (Ornstein-Uhlenbeck).
#     - wind_power: cubic power curve based on cut-in/rated/cut-out.
#     - SolarModel: clear-sky irradiance using Kasten-Young air-mass formula
#       (latitude + day-of-year + hour) with cloud cover & panel-temperature derating.
#     - VesselNavigator: haversine distance along Aegean waypoint routes,
#       computes lat/lon/heading/ETA in real time, ping-pongs at endpoints.

class WindModel:
    """Regional wind speed via mean-reverting random walk."""
    BASES = {"thrace": 7.5, "tinos": 10.5, "naxos": 7.0, "thessaly": 5.0, "crete": 6.5}
    def __init__(self):
        self.current = {r: v + random.gauss(0, 1.0) for r, v in self.BASES.items()}
    def tick(self):
        theta, sigma = 0.02, 0.18
        for r in self.current:
            mu = self.BASES[r]; w = self.current[r]
            self.current[r] = max(0.0, w + theta * (mu - w) + sigma * random.gauss(0, 1))
    def get(self, region, noise=0.5):
        return max(0.0, self.current.get(region, 5.0) + random.gauss(0, noise))

def wind_power(ws, cut_in, rated, cut_out, cap):
    """Cubic wind-power curve."""
    if ws < cut_in or ws > cut_out: return 0.0
    if ws >= rated: return cap
    return cap * ((ws - cut_in) / (rated - cut_in)) ** 3

class SolarModel:
    """Clear-sky GHI using Kasten-Young air-mass model."""
    def __init__(self, daytime_override=False):
        self.daytime = daytime_override
        self.cloud = {"thessaly": random.uniform(0.85, 1.0), "crete": random.uniform(0.88, 1.0)}
    def tick(self):
        for r in self.cloud:
            self.cloud[r] = max(0.4, min(1.0, self.cloud[r] + random.gauss(0, 0.008)))
    def irradiance(self, lat, hour_utc):
        h_local = 13.0 if self.daytime else (hour_utc + 3) % 24
        doy = 105
        decl = math.radians(23.45 * math.sin(math.radians(360 / 365 * (doy - 81))))
        ha = math.radians(15 * (h_local - 12.5))
        lat_r = math.radians(lat)
        sin_elev = math.sin(decl) * math.sin(lat_r) + math.cos(decl) * math.cos(lat_r) * math.cos(ha)
        if sin_elev <= 0.02: return 0.0
        am = 1.0 / (sin_elev + 0.50572 * (math.degrees(math.asin(sin_elev)) + 6.07995) ** -1.6364)
        return max(0.0, 1361 * 0.7 ** (am ** 0.678) * sin_elev)
    def power_kw(self, inv, hour_utc):
        ghi = self.irradiance(inv["lat"], hour_utc) * self.cloud.get(inv["region"], 0.9)
        h_local = 13.0 if self.daytime else (hour_utc + 3) % 24
        ambient = 15 + 8 * max(0, math.sin(math.radians(max(0, (h_local - 5)) / 14 * 180)))
        t_panel = ambient + 0.03 * ghi
        temp_factor = max(0.70, 1.0 - 0.004 * max(0, t_panel - 25))
        pwr = inv["cap_kw"] * (ghi / 1000.0) * temp_factor
        eff = (pwr / inv["cap_kw"] * 100) if ghi > 20 else 0.0
        return max(0, pwr + random.gauss(0, pwr * 0.005)), round(ghi, 1), round(t_panel, 1), round(eff, 1)

class VesselNavigator:
    """Haversine navigation along Aegean waypoint routes (ping-pong)."""
    def __init__(self, vessels):
        self.ships = []
        for v in vessels:
            total = self._route_nm(v["route"])
            self.ships.append({**v, "progress": v["start_pct"], "total_nm": total, "nm_per_sec": v["speed"]/3600.0})
    @staticmethod
    def _hav(p1, p2):
        la1, lo1 = math.radians(p1[0]), math.radians(p1[1])
        la2, lo2 = math.radians(p2[0]), math.radians(p2[1])
        dlat, dlon = la2 - la1, lo2 - lo1
        a = math.sin(dlat/2)**2 + math.cos(la1)*math.cos(la2)*math.sin(dlon/2)**2
        return 2 * 3440.065 * math.asin(math.sqrt(a))
    def _route_nm(self, route):
        return sum(self._hav(route[i], route[i+1]) for i in range(len(route)-1))
    def _interp(self, route, pct):
        if pct <= 0: return route[0][0], route[0][1], 0.0
        if pct >= 1: return route[-1][0], route[-1][1], 0.0
        total = self._route_nm(route); target = pct * total; accum = 0.0
        for i in range(len(route)-1):
            seg = self._hav(route[i], route[i+1])
            if accum + seg >= target:
                t = (target - accum) / seg if seg > 0 else 0
                lat = route[i][0] + t * (route[i+1][0] - route[i][0])
                lon = route[i][1] + t * (route[i+1][1] - route[i][1])
                hdg = math.degrees(math.atan2(route[i+1][1] - route[i][1], route[i+1][0] - route[i][0]))
                return lat, lon, (90 - hdg) % 360
            accum += seg
        return route[-1][0], route[-1][1], 0.0
    def tick(self, dt_sec):
        results = []
        for s in self.ships:
            s["progress"] += (s["nm_per_sec"] * dt_sec / s["total_nm"]) if s["total_nm"] > 0.001 else 0
            if s["progress"] >= 1.0:
                s["progress"] -= 1.0; s["route"] = list(reversed(s["route"]))
            elif s["progress"] <= 0.0:
                s["progress"] = 1.0 + s["progress"]; s["route"] = list(reversed(s["route"]))
            lat, lon, hdg = self._interp(s["route"], s["progress"])
            rem_nm = s["total_nm"] * max(0, 1 - s["progress"])
            eta_h = rem_nm / s["speed"] if s["speed"] > 0 else 0
            dest = s.get("destination", "Revithoussa LNG Terminal" if "LNG" in s["type"] else "Piraeus Port")
            results.append({
                "vessel_id": s["id"], "vessel_name": s["name"], "vessel_type": s["type"],
                "latitude": round(lat, 4), "longitude": round(lon, 4),
                "speed_knots": round(s["speed"] if s["total_nm"] > 0.001 else 0, 1), "heading_deg": round(hdg, 1),
                "destination": dest, "eta_hours": round(eta_h, 1), "cargo_status": s["cargo"],
            })
        return results

print("Physics models ready")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Anomaly engine
# Two layers of faults:
# 1. **Scripted incident** — `WT-NAX-07` bearing degradation that escalates over time (the headline story).
# 2. **Random anomalies** — N random assets per stream that misbehave with `ANOMALY_PROBABILITY` per cycle, tagged with a `fault_type` field for KQL filtering.

# CELL ********************

# >>> Two kinds of faults are injected into the data stream:
#     1. ScriptedIncident: WT-NAX-07 bearing degradation that escalates
#        over time (elevated -> WARNING -> CRITICAL). The headline story.
#     2. AnomalyEngine: random faults on N assets per type with a tunable
#        probability and severity. Each faulty event is tagged with a
#        'fault_type' field so KQL / the agent can filter on it.

class ScriptedIncident:
    # Progressive bearing degradation on a single turbine.
    # Demo-tuned: fires immediately and frequently. Severity still
    # escalates over time (elevated -> WARNING -> CRITICAL) so a longer
    # demo shows the fault getting worse.
    def __init__(self, enabled, target):
        self.enabled = enabled
        self.target = target
        self.t0 = time.time() if enabled else None
    def vibration_extra(self, turbine_id):
        if not self.enabled or turbine_id != self.target: return 0.0, None
        elapsed = time.time() - self.t0
        # Demo-tuned: frequent AND sharp - constant visible spikes for live demo
        if elapsed < 120:    prob, lo, hi = 0.12, 10.0, 15.0   # first 2 min: rare warnings
        elif elapsed < 360:  prob, lo, hi = 0.18, 15.0, 22.0   # 2-6 min:    escalating
        else:                prob, lo, hi = 0.18, 20.0, 30.0   # 6 min+:     critical sharp spikes
        if random.random() < prob:
            return random.uniform(lo, hi), "bearing_degradation"
        return 0.0, None
        if turbine_id == self.target:
            elapsed = time.time() - self.t0
            if elapsed < 120:    prob, lo, hi = 0.12, 10.0, 15.0
            elif elapsed < 360:  prob, lo, hi = 0.18, 15.0, 22.0
            else:                prob, lo, hi = 0.18, 20.0, 30.0
            if random.random() < prob:
                return random.uniform(lo, hi), "bearing_degradation"
            return 0.0, None
        if turbine_id == self.secondary:
            now = time.time()
            # Trigger a new spike window when due
            if now >= self.next_secondary_spike and now > self.secondary_spike_until:
                self.secondary_spike_until = now + random.uniform(6, 12)  # 6-12 sec spike burst
                self.secondary_spike_lo = random.uniform(18.0, 24.0)
                self.secondary_spike_hi = self.secondary_spike_lo + random.uniform(4.0, 8.0)
                self.next_secondary_spike = now + random.uniform(540, 720)  # next in 9-12 min
            if now <= self.secondary_spike_until:
                return random.uniform(self.secondary_spike_lo, self.secondary_spike_hi), "bearing_degradation"
            return 0.0, None
        return 0.0, None
        elapsed = time.time() - self.t0
        # Demo-tuned: ONE spike every 5 minutes (300s window, 10s spike duration)
        cycle = elapsed % 300
        if cycle < 10:
            # severity escalates over time
            if elapsed < 600:    lo, hi = 15.0, 22.0   # first 10 min: warning
            elif elapsed < 1200: lo, hi = 20.0, 28.0   # 10-20 min:    elevated
            else:                lo, hi = 25.0, 35.0   # 20+ min:      critical
            return random.uniform(lo, hi), "bearing_degradation"
        return 0.0, None
        elapsed = time.time() - self.t0
        # Demo-tuned: frequent AND sharp - constant visible spikes for live demo
        if elapsed < 120:    prob, lo, hi = 0.12, 10.0, 15.0   # first 2 min: rare warnings
        elif elapsed < 360:  prob, lo, hi = 0.18, 15.0, 22.0   # 2-6 min:    escalating
        else:                prob, lo, hi = 0.18, 20.0, 30.0   # 6 min+:     critical sharp spikes
        if random.random() < prob:
            return random.uniform(lo, hi), "bearing_degradation"
        return 0.0, None

class AnomalyEngine:
    """Picks N random assets per type and injects faults probabilistically."""
    def __init__(self):
        if not ENABLE_ANOMALIES:
            self.wind_set = set(); self.solar_set = set(); self.gas_set = set()
            return
        wind_pool = [t["id"] for t in WIND_TURBINES if t["id"] != SCRIPTED_INCIDENT_TURBINE]
        solar_pool = [s["id"] for s in SOLAR_INVERTERS]
        gas_pool = [g["id"] for g in GAS_PLANTS]
        self.wind_set  = set(random.sample(wind_pool,  min(ANOMALY_WIND_TURBINES, len(wind_pool))))
        self.solar_set = set(random.sample(solar_pool, min(ANOMALY_SOLAR_INVERTERS, len(solar_pool))))
        self.gas_set   = set(random.sample(gas_pool,   min(ANOMALY_GAS_PLANTS, len(gas_pool))))

    def fires(self):
        return random.random() < ANOMALY_PROBABILITY
    def severity(self):
        return random.uniform(ANOMALY_SEVERITY_MIN, ANOMALY_SEVERITY_MAX)

    def wind_anomaly(self, turbine_id, baseline_vib):
        if turbine_id in self.wind_set and self.fires():
            return baseline_vib * self.severity(), "vibration_spike"
        return baseline_vib, None

    def solar_anomaly(self, inverter_id, baseline_eff, baseline_pwr):
        if inverter_id in self.solar_set and self.fires():
            drop_factor = 1.0 / self.severity()
            return baseline_eff * drop_factor, baseline_pwr * drop_factor, "panel_soiling_or_string_fault"
        return baseline_eff, baseline_pwr, None

    def gas_anomaly(self, plant_id, baseline_co2):
        if plant_id in self.gas_set and self.fires():
            return baseline_co2 * (1 + (self.severity() - 1) * 0.3), "combustion_inefficient"
        return baseline_co2, None

scripted = ScriptedIncident(ENABLE_SCRIPTED_INCIDENT, SCRIPTED_INCIDENT_TURBINE)
anomalies = AnomalyEngine()

print(f'Scripted incident: ' + (SCRIPTED_INCIDENT_TURBINE if ENABLE_SCRIPTED_INCIDENT else 'OFF'))
if ENABLE_ANOMALIES:
    print('Random anomaly assets:')
    print('  wind turbines  :', sorted(anomalies.wind_set) or 'none')
    print('  solar inverters:', sorted(anomalies.solar_set) or 'none')
    print('  gas plants     :', sorted(anomalies.gas_set) or 'none')
    print(f'  probability    : {ANOMALY_PROBABILITY:.0%} per cycle')
    print(f'  severity       : {ANOMALY_SEVERITY_MIN}x to {ANOMALY_SEVERITY_MAX}x baseline')
else:
    print("Random anomalies: OFF")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Telemetry generators
# One function per stream. Each returns a list of JSON events with `stream_type` for Eventstream routing.

# CELL ********************

# === DEMO CONTROL FILES (read by generators each tick) ===
# Reads from AegeanPowerLH/Files/control/ regardless of attached default lakehouse.
import os
WS_ID  = "21dbf808-03bb-44d9-a8f4-ac6166b1ce08"
LH_ID  = "bd9c69ce-ee2b-45a9-854d-13696f476a96"  # AegeanPowerLH
ABFSS  = f"abfss://{WS_ID}@onelake.dfs.fabric.microsoft.com/{LH_ID}"
CTRL_LOCAL = "/lakehouse/default/Files/control"

def _read_remote(rel_path):
    """Read a small text file from AegeanPowerLH via Spark."""
    try:
        df = spark.read.text(f"{ABFSS}/Files/control/{rel_path}")
        rows = df.collect()
        return "\n".join(r.value for r in rows)
    except Exception:
        return ""

def get_failed_turbines():
    # Fast local mount path first
    try:
        p = f"{CTRL_LOCAL}/failed_turbines.txt"
        if os.path.exists(p):
            with open(p) as f:
                return {line.strip() for line in f if line.strip() and not line.startswith("#")}
    except Exception:
        pass
    # Fallback to remote ABFSS
    txt = _read_remote("failed_turbines.txt")
    return {line.strip() for line in txt.splitlines() if line.strip() and not line.startswith("#")}

def poseidon_dispatched():
    try:
        p = f"{CTRL_LOCAL}/dispatch_poseidon.txt"
        if os.path.exists(p):
            with open(p) as f:
                line = f.read().strip()
            if line:
                lat, lon = line.split(",")
                return float(lat), float(lon)
    except Exception:
        pass
    txt = _read_remote("dispatch_poseidon.txt").strip()
    if txt:
        try:
            lat, lon = txt.split(",")
            return float(lat), float(lon)
        except Exception:
            return None
    return None


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# >>> One generator function per stream. Each returns a list of JSON
#     events tagged with a 'stream_type' field. The Eventstream uses
#     that tag to route events to the correct KQL table:
#       WindTurbineTelemetry, SolarInverterTelemetry, GridTelemetry,
#       VesselPositions, EmissionsStream.

def gen_wind(now):
    failed_set = get_failed_turbines()
    events = []
    for t in WIND_TURBINES:
        ws = wind.get(t["region"])
        pwr = wind_power(ws, t["cut_in"], t["rated"], t["cut_out"], t["cap"])
        baseline_vib = random.uniform(1.8, 3.5)
        scripted_extra, scripted_fault = scripted.vibration_extra(t["id"])
        vib = baseline_vib + scripted_extra
        vib, anomaly_fault = anomalies.wind_anomaly(t["id"], vib)
        fault_type = scripted_fault or anomaly_fault or "NONE"

        if ws >= t["cut_in"] and ws <= t["cut_out"]:
            rpm = min(14.8, 4.5 + 10.3 * min(1, (ws - t["cut_in"]) / (t["rated"] - t["cut_in"])))
        else:
            rpm = 0
        ambient = 16 + 3 * math.sin(math.radians(((now.hour + 3) % 24 - 6) / 16 * 180))
        nacelle_t = ambient + 4 + pwr * 1.8 + random.gauss(0, 0.5)
        is_failed = t["id"] in failed_set
        if is_failed:
            pwr = 0.0; vib = 0.0; rpm = 0.0; fault_type = "DEMO_FORCED_FAILURE"
        events.append({
            "timestamp": now.isoformat(), "stream_type": "WindTurbineTelemetry",
            "turbine_id": t["id"], "plant_id": t["plant"],
            "power_mw": 0.0 if is_failed else round(max(0, pwr + random.gauss(0, 0.015)), 3),
            "wind_speed_ms": round(ws, 1), "vibration_mm_s": 0.0 if is_failed else round(vib, 2),
            "rotor_rpm": 0.0 if is_failed else round(max(0, rpm + random.gauss(0, 0.15)), 1),
            "nacelle_temp_c": round(nacelle_t, 1),
            "latitude": t["lat"], "longitude": t["lon"],
            "fault_type": fault_type,
        })
    return events

def gen_solar(now):
    h_utc = now.hour + now.minute / 60.0
    events = []
    for inv in SOLAR_INVERTERS:
        pwr, ghi, t_panel, eff = solar.power_kw(inv, h_utc)
        eff, pwr, fault_type = anomalies.solar_anomaly(inv["id"], eff, pwr)
        events.append({
            "timestamp": now.isoformat(), "stream_type": "SolarInverterTelemetry",
            "inverter_id": inv["id"], "plant_id": inv["plant"],
            "power_kw": round(max(0, pwr), 1), "irradiance_wm2": ghi,
            "panel_temp_c": t_panel, "efficiency_pct": round(eff, 1),
            "latitude": inv["lat"], "longitude": inv["lon"],
            "fault_type": fault_type,
        })
    return events

def gen_grid(now):
    h_local = (now.hour + 3) % 24
    demand_factor = 0.65 + 0.35 * math.sin(math.radians(max(0, (h_local - 4)) / 16 * 180))
    events = []
    for g in ISLAND_GRIDS:
        load = g["base_load"] * demand_factor * random.uniform(0.98, 1.02)
        solar_effect = 0.08 * math.sin(math.radians(max(0, (h_local - 6)) / 12 * 180)) if 6 <= h_local <= 18 else 0
        wind_var = random.uniform(-0.04, 0.06)
        gen = load * (1.0 + solar_effect + wind_var + random.gauss(0, 0.01))
        balance = gen - load
        freq = 50.0 + balance / (g["inertia"] * 0.01) + random.gauss(0, 0.005)
        v_nom = 400 if g["id"] == "GR-MAIN" else 150 if g["id"] == "GR-CRE" else 20
        voltage = v_nom * (1 + random.gauss(0, 0.003))
        events.append({
            "timestamp": now.isoformat(), "stream_type": "GridTelemetry",
            "grid_id": g["id"], "grid_name": g["name"],
            "frequency_hz": round(freq, 3), "load_mw": round(max(0, load), 1),
            "generation_mw": round(max(0, gen), 1), "voltage_kv": round(voltage, 1),
            "balance_mw": round(balance, 2),
        })
    return events

def gen_vessels(now):
    # Demo: re-route Poseidon Service when dispatch flag is set (sea-only waypoints)
    target = poseidon_dispatched()
    if target is not None:
        for s in nav.ships:
            if s["id"] == "VE-SVC-01" and not s.get("_dispatched"):
                # Fixed open-sea route: Piraeus -> south of Cyclades -> NAX-04
                s["route"] = [
                    (37.94, 23.62),
                    (37.78, 23.72),
                    (37.55, 23.95),
                    (37.30, 24.20),
                    (37.10, 24.55),
                    (37.00, 24.95),
                    (37.00, 25.30),
                    (37.05, 25.45),
                    target,
                ]
                s["total_nm"] = nav._route_nm(s["route"])
                s["progress"] = 0.0
                s["destination"] = "WT-NAX-04 (Naxos Wind Farm) - DISPATCHED"
                s["_dispatched"] = True
    positions = nav.tick(VESSEL_EVERY_N * INTERVAL_SECONDS * 8)  # demo: 8x time-warp for visible movement
    for p in positions:
        p["timestamp"] = now.isoformat()
        p["stream_type"] = "VesselPositions"
    return positions

def gen_emissions(now):
    h_local = (now.hour + 3) % 24
    hours_today = h_local + now.minute / 60.0
    events = []
    for p in GAS_PLANTS:
        lf = max(0.25, min(0.85, 0.40 + 0.30 * math.sin(math.radians(max(0, (h_local - 5)) / 14 * 180)) + random.gauss(0, 0.02)))
        pwr = p["cap_mw"] * lf
        co2_hr = pwr * p["ef"] * 1000
        co2_hr, fault_type = anomalies.gas_anomaly(p["id"], co2_hr)
        avg_lf = 0.30 + 0.20 * min(1.0, hours_today / 14)
        cum_t = p["cap_mw"] * avg_lf * p["ef"] * hours_today
        comp = (cum_t / p["ets_daily"]) * 100
        events.append({
            "timestamp": now.isoformat(), "stream_type": "EmissionsStream",
            "plant_id": p["id"], "plant_name": p["name"],
            "power_output_mw": round(pwr, 1), "co2_kg_per_hour": round(co2_hr, 0),
            "cumulative_co2_tonnes_today": round(cum_t, 1),
            "ets_daily_allowance_tonnes": p["ets_daily"],
            "compliance_pct": round(min(comp, 150), 1), "fuel_type": "Natural Gas",
            "fault_type": fault_type,
        })
    return events

print("Generators ready")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Run simulator
# Sends batched events to the Fabric Eventstream. **Interrupt the cell to stop cleanly.**

# CELL ********************

# >>> The main simulator loop.
#     Each base tick: advance physics models, decide which streams
#     are due (per-stream cadence), generate events, batch them, send
#     to the EventHub. Prints a summary + any active faults every
#     PRINT_EVERY_N_CYCLES ticks. Stop the cell to exit cleanly.

wind = WindModel()
solar = SolarModel(daytime_override=FORCE_DAYTIME)
nav = VesselNavigator(VESSELS)

producer = EventHubProducerClient.from_connection_string(EVENTHUB_CONNECTION_STRING)

print('Starting Aegean Power simulator')
print(f'  Base interval : {INTERVAL_SECONDS}s | Max cycles: ' + (str(MAX_CYCLES) if MAX_CYCLES else 'infinite'))
print(f'  Cadence (s)   : wind={WIND_EVERY_N*INTERVAL_SECONDS}, solar={SOLAR_EVERY_N*INTERVAL_SECONDS}, grid={GRID_EVERY_N*INTERVAL_SECONDS}, vessels={VESSEL_EVERY_N*INTERVAL_SECONDS}, emissions={EMISSIONS_EVERY_N*INTERVAL_SECONDS}')
print(f'  Solar mode    : ' + ('forced daytime' if FORCE_DAYTIME else 'real clock'))
print("-" * 70)

tick = 0
total_events_sent = 0
try:
    while MAX_CYCLES == 0 or tick < MAX_CYCLES:
        now = datetime.now(timezone.utc)
        batch = []

        wind.tick(); solar.tick()

        if tick % WIND_EVERY_N == 0:      batch.extend(gen_wind(now))
        if tick % SOLAR_EVERY_N == 0:     batch.extend(gen_solar(now))
        if tick % GRID_EVERY_N == 0:      batch.extend(gen_grid(now))
        if tick % VESSEL_EVERY_N == 0:    batch.extend(gen_vessels(now))
        if tick % EMISSIONS_EVERY_N == 0: batch.extend(gen_emissions(now))

        if batch:
            eh_batch = producer.create_batch()
            for ev in batch:
                eh_batch.add(EventData(json.dumps(ev, default=str)))
            producer.send_batch(eh_batch)
            total_events_sent += len(batch)

        if PRINT_EVERY_N_CYCLES > 0 and tick % PRINT_EVERY_N_CYCLES == 0 and batch:
            ts = now.strftime("%H:%M:%S")
            wind_ev  = [e for e in batch if e.get("stream_type") == "WindTurbineTelemetry"]
            solar_ev = [e for e in batch if e.get("stream_type") == "SolarInverterTelemetry"]
            faults   = [e for e in batch if e.get("fault_type") and e.get("fault_type") != "NONE"]
            w_mw = sum(e['power_mw'] for e in wind_ev)
            s_mw = sum(e['power_kw'] for e in solar_ev) / 1000
            print(f"[{ts}] tick={tick:5d}  wind={w_mw:6.1f}MW  solar={s_mw:6.1f}MW  events={len(batch):3d}  faults={len(faults)}  total_sent={total_events_sent}")
            for e in faults:
                aid = e.get('turbine_id') or e.get('inverter_id') or e.get('plant_id')
                print(f"           FAULT: {aid} -> {e['fault_type']}")

        tick += 1
        time.sleep(INTERVAL_SECONDS)

except KeyboardInterrupt:
    print("\nStopped by user.")
finally:
    producer.close()
    print(f"Total: {tick} ticks, {total_events_sent} events sent.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

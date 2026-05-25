# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {}
# META   }
# META }

# CELL ********************

# Uses the notebook's default lakehouse (bind AegeanPowerLH per README step 4)
CSV = 'Files/data'
print(f'Reading from: {CSV}')
df = spark.read.option('header', True).option('inferSchema', True).csv(f'{CSV}/power_plants.csv')
df.show()
print(f'Row count: {df.count()}')

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import col

# Uses the notebook's default lakehouse (bind AegeanPowerLH per README step 4)
CSV = 'Files/data'

tables = [
    ('power_plants.csv', 'power_plants', {'capacity_mw':'double','latitude':'double','longitude':'double','commissioning_year':'int'}),
    ('wind_turbines.csv', 'wind_turbines', {'capacity_mw':'double','hub_height_m':'double','rotor_diameter_m':'double','cut_in_speed_ms':'double','rated_speed_ms':'double','cut_out_speed_ms':'double','latitude':'double','longitude':'double'}),
    ('solar_inverters.csv', 'solar_inverters', {'capacity_kw':'double','panel_tilt_deg':'double','panel_azimuth_deg':'double','latitude':'double','longitude':'double'}),
    ('substations.csv', 'substations', {'voltage_kv':'double','latitude':'double','longitude':'double'}),
    ('island_grids.csv', 'island_grids', {'population':'int','peak_demand_mw':'double','installed_capacity_mw':'double','nominal_frequency_hz':'double','latitude':'double','longitude':'double'}),
    ('vessels.csv', 'vessels', {'capacity_m3':'double','current_cargo_m3':'double','speed_knots':'double'}),
    ('maintenance_orders.csv', 'maintenance_orders', {'cost_eur':'double'}),
    ('emissions_ledger.csv', 'emissions_ledger', {'co2_tonnes':'double','ets_allowance_tonnes':'double','fuel_consumed_mwh':'double','emission_factor_tco2_per_mwh':'double','compliance_pct':'double'})
]

for csv_file, tbl, overrides in tables:
    df = spark.read.option('header', True).option('inferSchema', True).csv(f'{CSV}/{csv_file}')
    for c, dtype in overrides.items():
        df = df.withColumn(c, col(c).cast(dtype))
    df.write.mode('overwrite').format('delta').saveAsTable(tbl)
    print(f'OK: {tbl} = {df.count()} rows')

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

print('=== ALL TABLES ===')
for t in spark.catalog.listTables():
    print(f'  {t.name}: {spark.table(t.name).count()} rows')

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

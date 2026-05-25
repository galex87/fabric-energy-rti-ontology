# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "74b1118c-ad81-44e8-bcc6-c16465e827ef",
# META       "default_lakehouse_name": "AegeanPowerLH_Raw",
# META       "default_lakehouse_workspace_id": "21dbf808-03bb-44d9-a8f4-ac6166b1ce08",
# META       "known_lakehouses": [
# META         {
# META           "id": "74b1118c-ad81-44e8-bcc6-c16465e827ef"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# # Aegean Power - Load Raw CSVs to Delta Tables
# Reads obfuscated master data CSVs from Files/csv/ and creates managed Delta tables.

# CELL ********************

from pyspark.sql.functions import col

CSV_BASE = "Files/csv"

tables = [
    ("wt_master.csv", "wt_master", {"rated_kw": "double", "ht_hub": "double", "dia_rot": "double", "spd_min": "double", "spd_nom": "double", "spd_max": "double", "coord_x": "double", "coord_y": "double"}),
    ("pv_master.csv", "pv_master", {"rated_kw": "double", "ang_tilt": "double", "ang_azm": "double", "coord_x": "double", "coord_y": "double"}),
    ("gen_sites.csv", "gen_sites", {"cap_inst": "double", "geo_lat": "double", "geo_lon": "double", "yr_comm": "int"}),
    ("net_config.csv", "net_config", {"pop_cnt": "int", "pk_load": "double", "tot_cap": "double", "freq_nom": "double", "geo_lat": "double", "geo_lon": "double"}),
    ("vsl_tracking.csv", "vsl_tracking", {"cap_vol": "int", "cur_vol": "int", "spd_cur": "double"}),
    ("srv_activity.csv", "srv_activity", {"amt_total": "double"}),
    ("node_infra.csv", "node_infra", {"vlt_lvl": "double", "geo_lat": "double", "geo_lon": "double"}),
    ("env_reporting.csv", "env_reporting", {"co2_qty": "double", "ets_alloc": "double", "fuel_qty": "double", "ef_ratio": "double", "pct_compl": "double"})
]

for csv_file, table_name, overrides in tables:
    path = f"{CSV_BASE}/{csv_file}"
    df = spark.read.option("header", True).option("inferSchema", True).csv(path)
    for col_name, dtype in overrides.items():
        if col_name in df.columns:
            df = df.withColumn(col_name, col(col_name).cast(dtype))
    df.write.mode("overwrite").option("overwriteSchema", "true").format("delta").saveAsTable(table_name)
    print(f"Created table '{table_name}' with {df.count()} rows, {len(df.columns)} columns")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

for t in spark.catalog.listTables():
    count = spark.table(t.name).count()
    cols = len(spark.table(t.name).columns)
    print(f"  {t.name}: {count} rows, {cols} columns")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

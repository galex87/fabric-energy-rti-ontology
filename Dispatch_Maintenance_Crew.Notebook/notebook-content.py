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

# MARKDOWN ********************

# # Dispatch Maintenance Crew
# 
# Triggered by the AegeanPower Operations Agent when a turbine reports fault_type == DEMO_FORCED_FAILURE.
# Writes a control file the simulator polls to dispatch Poseidon Service from Piraeus.

# CELL ********************

import notebookutils
# Resolve AegeanPowerLH via ABFSS so we don't depend on /lakehouse/default/ mount.
_lh = notebookutils.lakehouse.get("AegeanPowerLH")
_ws = _lh.get('workspaceId') or notebookutils.runtime.context['currentWorkspaceId']
CTRL = f"abfss://{_ws}@onelake.dfs.fabric.microsoft.com/{_lh['id']}/Files/control"
DISPATCH = f'{CTRL}/dispatch_poseidon.txt'

existing = ''
if notebookutils.fs.exists(DISPATCH):
    existing = notebookutils.fs.head(DISPATCH, 1024).strip()
if existing:
    print(f'SKIP: dispatch already in progress -> {existing!r}')
else:
    notebookutils.fs.mkdirs(CTRL)
    notebookutils.fs.put(DISPATCH, '37.065,25.478', True)  # WT-NAX-04 coordinates
    print('DISPATCHED: Poseidon Service -> 37.065, 25.478 (Naxos)')
    print('Watch the Fleet Map - the bubble will start moving SE within ~10 s.')

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

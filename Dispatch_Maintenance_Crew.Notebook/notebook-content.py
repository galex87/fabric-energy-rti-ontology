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

import os
CTRL = '/lakehouse/default/Files/control'
DISPATCH = f'{CTRL}/dispatch_poseidon.txt'

if os.path.exists(DISPATCH) and open(DISPATCH).read().strip():
    print(f'SKIP: dispatch already in progress -> {open(DISPATCH).read().strip()!r}')
else:
    os.makedirs(CTRL, exist_ok=True)
    with open(DISPATCH, 'w') as f:
        f.write('37.065,25.478')  # WT-NAX-04 coordinates
    print('DISPATCHED: Poseidon Service -> 37.065, 25.478 (Naxos)')
    print('Watch the Fleet Map - the bubble will start moving SE within ~10 s.')

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

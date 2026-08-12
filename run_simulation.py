import os
import sys
import random
import traci
from sumolib import checkBinary
#this is from the github
# 1. FIND SUMO AND TRACI ON YOUR SYSTEM
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Error: Please declare environment variable 'SUMO_HOME'")

# 2. WRITE THE 4-VEHICLE ROUTE FILE
routes_xml = """<?xml version="1.0" encoding="UTF-8"?>
<routes>
    <vType id="car" vClass="passenger" length="4.5" accel="2.6" decel="4.5" maxSpeed="14.0" color="yellow" guiShape="passenger/sedan"/>
    <vType id="truck" vClass="truck" length="12.0" accel="0.8" decel="3.0" maxSpeed="8.0" color="blue" guiShape="truck"/>
    <vType id="bike" vClass="motorcycle" length="3.0" accel="3.5" decel="5.0" maxSpeed="16.0" color="green" guiShape="motorcycle"/>
    <vType id="ambulance" vClass="authority" length="6.5" accel="3.0" decel="4.5" maxSpeed="18.0" color="red" guiShape="emergency"/>
</routes>
"""
with open("my_routes.rou.xml", "w") as f:
    f.write(routes_xml)

# 3. LAUNCH SUMO-GUI SAFELY WITH ABSOLUTE PATHS
try:
    sumoBinary = checkBinary('sumo-gui')
    # Get the exact folder where this Python script is saved
    current_folder = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_folder, "sim.sumocfg")
    
    sumo_cmd = [
        sumoBinary, 
        "-c", config_path, 
        "--delay", "150", 
        "--ignore-route-errors", "true"
    ]
    traci.start(sumo_cmd)
except Exception as e:
    sys.exit(f"Failed to start SUMO. Error: {e}")

# 4. SET UP DYNAMIC ROUTING 
print("Running simulation with dynamic random routing for 4 vehicle types...")
all_edges = [e for e in traci.edge.getIDList() if not e.startswith(":")]
v_types = ["car", "truck", "bike", "ambulance"]

step = 0
veh_id = 0

# 5. RUN THE SIMULATION LOOP
while traci.simulation.getTime() < 86400:
    traci.simulationStep()
    
    if step % 5 == 0:
        start_edge = random.choice(all_edges)
        end_edge = random.choice(all_edges)
        
        if start_edge != end_edge:
            v_type = random.choice(v_types)
            try:
                route = traci.simulation.findRoute(start_edge, end_edge, vType=v_type)
                if route.edges:
                    route_id = f"route_{veh_id}"
                    traci.route.add(route_id, route.edges)
                    traci.vehicle.add(f"veh_{veh_id}", route_id, typeID=v_type)
                    veh_id += 1
            except traci.exceptions.TraCIException:
                pass

    step += 1

traci.close()

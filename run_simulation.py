import os
import sys
import random
import traci
from sumolib import checkBinary

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
    <vType id="sedan" vClass="passenger" guiShape="passenger/sedan" length="4.5" width="1.8" maxSpeed="22.2" accel="2.6" decel="4.5" color="255,255,0"/>
    <vType id="hatchback" vClass="passenger" guiShape="passenger/hatchback" length="3.8" width="1.7" maxSpeed="20.0" accel="2.8" decel="4.5" color="0,255,255"/>
    <vType id="suv" vClass="evehicle" guiShape="passenger/wagon" length="4.8" width="1.9" maxSpeed="25.0" accel="2.5" decel="4.2" color="0,0,255"/>
    <vType id="sports_car" vClass="passenger" guiShape="passenger" length="4.2" width="1.9" maxSpeed="33.3" accel="4.0" decel="5.0" color="255,0,0"/>
    <vType id="taxi" vClass="taxi" guiShape="passenger/sedan" length="4.4" width="1.8" maxSpeed="20.0" accel="2.5" decel="4.5" color="255,200,0"/>
    <vType id="e_car" vClass="evehicle" guiShape="passenger/hatchback" length="4.0" width="1.8" maxSpeed="22.0" accel="3.2" decel="4.8" color="0,255,128"/>
    <vType id="motorcycle" vClass="motorcycle" guiShape="motorcycle" length="2.2" width="0.9" maxSpeed="25.0" accel="4.5" decel="5.5" color="255,0,255"/>
    <vType id="scooter" vClass="moped" guiShape="moped" length="1.8" width="0.8" maxSpeed="15.0" accel="3.0" decel="5.0" color="255,255,0"/>
    <vType id="auto_rickshaw" vClass="custom1" guiShape="rickshaw" length="2.7" width="1.3" maxSpeed="12.5" accel="1.8" decel="4.0" color="255,255,0"/>
    <vType id="e_rickshaw" vClass="custom2" guiShape="rickshaw" length="2.6" width="1.2" maxSpeed="9.0" accel="1.2" decel="3.8" color="0,255,0"/>
    <vType id="bicycle" vClass="bicycle" guiShape="bicycle" length="1.6" width="0.6" maxSpeed="5.5" accel="1.2" decel="3.0" color="0,128,128"/>
    <vType id="fire_truck" vClass="authority" guiShape="firebrigade" length="10.0" width="2.5" maxSpeed="20.0" accel="1.5" decel="3.8" color="200,0,0"/>
    <vType id="police_car" vClass="authority" guiShape="police" length="4.8" width="1.8" maxSpeed="28.0" accel="3.5" decel="5.0" color="0,0,0"/>
    <vType id="tractor" vClass="custom1" guiShape="truck" length="4.0" width="2.0" maxSpeed="8.0" accel="0.8" decel="2.5" color="165,42,42"/>
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
v_types = ["car", "truck", "bike", "ambulance", "sedan","hatchback","suv","sports_car", "taxi","e_car","motorcycle","scooter","auto_rickshaw","e_rickshaw","bicycle","fire_truck","police_car","tractor"]

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

#demo msg

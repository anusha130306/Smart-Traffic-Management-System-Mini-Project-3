import os
import random
import xml.etree.ElementTree as ET
import traci

# Project and file paths
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ROUTE_FILE = os.path.join(PROJECT_DIR, "Editfile.rou.xml")
SUMO_CONFIG = os.path.join(PROJECT_DIR, "Visuals.sumocfg")

# Simulation settings
SIMULATION_TIME = 300
NUMBER_OF_VEHICLES = 500

# Incoming edges of the junction
INCOMING_EDGES = ["E0", "E3", "E4", "E7"]

# Valid routes for each incoming edge
VALID_ROUTES = {
    "E0": [["E0", "E5"], ["E0", "E2"], ["E0", "E6"]],
    "E3": [["E3", "E6"], ["E3", "E1"], ["E3", "E5"]],
    "E4": [["E4", "E2"], ["E4", "E6"], ["E4", "E1"]],
    "E7": [["E7", "E1"], ["E7", "E5"], ["E7", "E2"]]
}

# Vehicle type distribution
VEHICLE_TYPES = [
    ("car", 55),
    ("motorcycle", 25),
    ("truck", 10),
    ("bus", 5),
    ("van", 5)
]

def random_vehicle_type():
    types = []
    for vehicle_type, probability in VEHICLE_TYPES:
        types.extend([vehicle_type] * probability)
    return random.choice(types)


def generate_random_traffic():
    print("Generating traffic...")
    routes = ET.Element("routes")

    # Define vehicle types
    ET.SubElement(routes, "vType",id="car",vClass="passenger",accel="2.6",decel="4.5",sigma="0.5",length="4.5",minGap="2.5",maxSpeed="13.89")
    ET.SubElement(routes, "vType",id="motorcycle",vClass="motorcycle",accel="3.0",decel="5.0",sigma="0.5",length="2.5",minGap="1.0",maxSpeed="16.67")
    ET.SubElement(routes, "vType",id="truck",vClass="truck",accel="1.0",decel="3.5",sigma="0.5",length="10.0",minGap="3.0",maxSpeed="11.11")
    ET.SubElement(routes, "vType",id="bus",vClass="bus",accel="1.2",decel="4.0",sigma="0.5",length="12.0",minGap="3.0",maxSpeed="12.5")
    ET.SubElement(routes, "vType",id="van",vClass="delivery",accel="2.0",decel="4.0",sigma="0.5",length="5.5",minGap="2.5",maxSpeed="13.89")

    vehicles = []

    # Generate vehicles with random routes and departure times
    for i in range(NUMBER_OF_VEHICLES):
        vehicle_id = f"vehicle_{i}"
        start_edge = random.choice(INCOMING_EDGES)
        route = random.choice(VALID_ROUTES[start_edge])
        vehicle_type = random_vehicle_type()

        depart_time = random.uniform(0, SIMULATION_TIME - 1)

        vehicles.append(
            (depart_time, vehicle_id, vehicle_type, route)
        )

    vehicles.sort(key=lambda x: x[0])

    # Add routes and vehicles to the route file
    for i, (depart_time, vehicle_id, vehicle_type, route) in enumerate(vehicles):
        route_id = f"route_{i}"

        ET.SubElement(
            routes,
            "route",
            id=route_id,
            edges=" ".join(route)
        )

        ET.SubElement(
            routes,
            "vehicle",
            id=vehicle_id,
            type=vehicle_type,
            route=route_id,
            depart=f"{depart_time:.2f}",
            departLane="random",
            departSpeed="random"
        )

    # Save the generated route file
    tree = ET.ElementTree(routes)
    ET.indent(tree, space="    ")

    tree.write(
        ROUTE_FILE,
        encoding="UTF-8",
        xml_declaration=True
    )

    print(f"Generated {NUMBER_OF_VEHICLES} vehicles")
    print(f"Route file: {ROUTE_FILE}")

def start_sumo():
    # Check SUMO configuration
    if not os.path.exists(SUMO_CONFIG):
        print("ERROR: Visuals.sumocfg not found")
        print(SUMO_CONFIG)
        return False

    # Check SUMO installation
    if "SUMO_HOME" not in os.environ:
        print("ERROR: SUMO_HOME is not set")
        return False

    sumo_binary = os.path.join(
        os.environ["SUMO_HOME"],
        "bin",
        "sumo-gui.exe"
    )

    if not os.path.exists(sumo_binary):
        print("ERROR: sumo-gui.exe not found")
        print(sumo_binary)
        return False

    print("Starting SUMO...")

    try:
        traci.start([
            sumo_binary,
            "-c", SUMO_CONFIG,
            "--delay", "100",
            "--step-length", "0.01",
            "--lateral-resolution", "0.01"
        ])

        return True

    except Exception as e:
        print("ERROR starting SUMO:")
        print(e)
        return False


def run_simulation():
    print("AI TRAFFIC MANAGEMENT SYSTEM")
    print("-----------------------------")

    # Generate random traffic
    generate_random_traffic()

    # Start SUMO
    if not start_sumo():
        return

    print("Simulation started")

    # Run simulation
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

    traci.close()

    print("Simulation finished")


if __name__ == "__main__":
    run_simulation()
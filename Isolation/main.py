import os
import random
import xml.etree.ElementTree as ET
import traci


# ============================================================
# PROJECT FOLDER
# ============================================================

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# FILE PATHS
# ============================================================

NET_FILE = os.path.join(
    PROJECT_DIR,
    "Networkcode.net.xml"
)

ROUTE_FILE = os.path.join(
    PROJECT_DIR,
    "Editfile.rou.xml"
)

SUMO_CONFIG = os.path.join(
    PROJECT_DIR,
    "Visuals.sumocfg"
)


# ============================================================
# SIMULATION SETTINGS
# ============================================================

SIMULATION_TIME = 300
NUMBER_OF_VEHICLES = 500


# ============================================================
# YOUR NETWORK EDGES
# ============================================================

INCOMING_EDGES = [
    "E0",
    "E3",
    "E4",
    "E7"
]

OUTGOING_EDGES = [
    "E1",
    "E2",
    "E5",
    "E6"
]


# ============================================================
# VALID ROUTES FROM YOUR NETWORK
# ============================================================

VALID_ROUTES = {

    "E0": [
        ["E0", "E5"],
        ["E0", "E2"],
        ["E0", "E6"]
    ],

    "E3": [
        ["E3", "E6"],
        ["E3", "E1"],
        ["E3", "E5"]
    ],

    "E4": [
        ["E4", "E2"],
        ["E4", "E6"],
        ["E4", "E1"]
    ],

    "E7": [
        ["E7", "E1"],
        ["E7", "E5"],
        ["E7", "E2"]
    ]
}


# ============================================================
# VEHICLE TYPE PROBABILITIES
# ============================================================

VEHICLE_TYPES = [
    ("car", 55),
    ("motorcycle", 25),
    ("truck", 10),
    ("bus", 5),
    ("van", 5)
]


# ============================================================
# RANDOM VEHICLE TYPE
# ============================================================

def random_vehicle_type():

    types = []

    for vehicle_type, probability in VEHICLE_TYPES:
        types.extend([vehicle_type] * probability)

    return random.choice(types)


# ============================================================
# GENERATE RANDOM TRAFFIC
# ============================================================

def generate_random_traffic():

    print("Generating random traffic...")

    routes = ET.Element("routes")

    # --------------------------------------------------------
    # CAR
    # --------------------------------------------------------

    ET.SubElement(
        routes,
        "vType",
        id="car",
        vClass="passenger",
        accel="2.6",
        decel="4.5",
        sigma="0.5",
        length="4.5",
        minGap="2.5",
        maxSpeed="13.89"
    )

    # --------------------------------------------------------
    # MOTORCYCLE
    # --------------------------------------------------------

    ET.SubElement(
        routes,
        "vType",
        id="motorcycle",
        vClass="motorcycle",
        accel="3.0",
        decel="5.0",
        sigma="0.5",
        length="2.5",
        minGap="1.0",
        maxSpeed="16.67"
    )

    # --------------------------------------------------------
    # TRUCK
    # --------------------------------------------------------

    ET.SubElement(
        routes,
        "vType",
        id="truck",
        vClass="truck",
        accel="1.0",
        decel="3.5",
        sigma="0.5",
        length="10.0",
        minGap="3.0",
        maxSpeed="11.11"
    )

    # --------------------------------------------------------
    # BUS
    # --------------------------------------------------------

    ET.SubElement(
        routes,
        "vType",
        id="bus",
        vClass="bus",
        accel="1.2",
        decel="4.0",
        sigma="0.5",
        length="12.0",
        minGap="3.0",
        maxSpeed="12.5"
    )

    # --------------------------------------------------------
    # VAN
    # --------------------------------------------------------

    ET.SubElement(
        routes,
        "vType",
        id="van",
        vClass="delivery",
        accel="2.0",
        decel="4.0",
        sigma="0.5",
        length="5.5",
        minGap="2.5",
        maxSpeed="13.89"
    )

    # --------------------------------------------------------
    # CREATE VEHICLES
    # --------------------------------------------------------

    vehicles = []

    for i in range(NUMBER_OF_VEHICLES):

        vehicle_id = f"vehicle_{i}"

        # Random incoming edge
        start_edge = random.choice(INCOMING_EDGES)

        # Random valid route
        route = random.choice(
            VALID_ROUTES[start_edge]
        )

        # Random vehicle type
        vehicle_type = random_vehicle_type()

        # Random departure time
        depart_time = random.uniform(
            0,
            SIMULATION_TIME - 1
        )

        vehicles.append(
            (
                depart_time,
                vehicle_id,
                vehicle_type,
                route
            )
        )

    # Sort according to departure time
    vehicles.sort(
        key=lambda x: x[0]
    )

    # --------------------------------------------------------
    # WRITE VEHICLES
    # --------------------------------------------------------

    for i, (
        depart_time,
        vehicle_id,
        vehicle_type,
        route
    ) in enumerate(vehicles):

        route_id = f"route_{i}"

        # Route
        ET.SubElement(
            routes,
            "route",
            id=route_id,
            edges=" ".join(route)
        )

        # Vehicle
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

    # --------------------------------------------------------
    # SAVE ROUTE FILE
    # --------------------------------------------------------

    tree = ET.ElementTree(routes)

    ET.indent(
        tree,
        space="    "
    )

    tree.write(
        ROUTE_FILE,
        encoding="UTF-8",
        xml_declaration=True
    )

    print(
        f"Generated {NUMBER_OF_VEHICLES} vehicles."
    )

    print(
        f"Route file: {ROUTE_FILE}"
    )


# ============================================================
# START SUMO
# ============================================================

def start_sumo():

    print(
        f"SUMO configuration: {SUMO_CONFIG}"
    )

    # Check configuration exists
    if not os.path.exists(SUMO_CONFIG):

        print("ERROR: Visuals.sumocfg was not found!")

        print(
            "Expected location:"
        )

        print(SUMO_CONFIG)

        return False

    sumo_cmd = [

        "sumo-gui",

        "-c",
        SUMO_CONFIG,

        "--delay",
        "100",

        "--step-length",
        "0.01",

        "--lateral-resolution",
        "0.01"
    ]

    print("Starting SUMO...")

    traci.start(
        sumo_cmd,
        cwd=PROJECT_DIR
    )

    return True


# ============================================================
# RUN SIMULATION
# ============================================================

def run_simulation():

    print("--------------------------------")
    print("AI TRAFFIC MANAGEMENT SYSTEM")
    print("--------------------------------")

    print(
        f"Project folder: {PROJECT_DIR}"
    )

    # Generate traffic
    generate_random_traffic()

    # Start SUMO
    if not start_sumo():
        return

    print("Simulation started.")

    while traci.simulation.getMinExpectedNumber() > 0:

        traci.simulationStep()

        # ====================================================
        # YOUR AI TRAFFIC CONTROL CODE WILL GO HERE
        # ====================================================

    traci.close()

    print("Simulation finished.")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    run_simulation()
# Finalised code with logic :

import math
import os 
import random 
import time 
import traci 
import xml.etree.ElementTree as ET

# xxxxxxxxxxxx Files from the local ( External files )
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ROUTE_FILE = os.path.join(PROJECT_DIR, "Editfile.rou.xml") #Route file 
SUMO_CONFIG = os.path.join(PROJECT_DIR, "Visuals.sumocfg") #Visuals file Main edit file 
GUI_SETTINGS_FILE = os.path.join(PROJECT_DIR, "gui_settings.xml") # guiSettings file 
BACKGROUND_IMAGE = os.path.join(PROJECT_DIR, "IsolationArielImage.png") # background image 

# xxxxxxxxxxxx Simulation Settings xxxxxxxxxxxxx 
SIMULATION_TIME = 300 #in seconds 
NUMBER_OF_VEHICLES = 300
STEP_LENGTH = 0.1 
GUI_DELAY_MS = 1000 #1000 miliS = 1 S 

VIEW_X, VIEW_Y, VIEW_ZOOM, VIEW_ANGLE = 0,0,150,0
IMAGE_WIDTH, IMAGE_HEIGHT = 210.12, 189.22  #Background image 
USE_GUI = os.environ.get("USE_GUI", "1")== "1"

# xxxxxxxxxxxx Default GUI Settings xxxxxxxxxxxx
#For lables 
TEXT_DISTANCE = 4.0 
PANEL_WIDTH = 17.0
PANEL_HEIGHT = 14.0
CIRCLE_RADIUS = 1.6
HALO_RADIUS = 2.6
#COLOURS 
COLOUR_RED = (220, 30, 30, 255)
COLOUR_RED_DIM = (90, 0, 0, 255) #Blinking        
COLOUR_GREEN = (0, 200, 0, 255)
COLOUR_YELLOW = (255, 200, 0, 255)
COLOUR_PANEL = (0, 0, 0, 255) #Black          
COLOUR_TEXT = (255, 255, 255, 255) #White         
COLOUR_HALO = (255, 255, 255, 255) #white

# xxxxxxxxxxx Road layout and paths xxxxxxxxxxx
INCOMING_EDGES = ["E2", "E4", "E6", "E8"]
VALID_ROUTES = {
    "E2": [["E2", "E3"], ["E2", "E5"], ["E2", "E7"]],
    "E4": [["E4", "E5"], ["E4", "E7"], ["E4", "E1"]],
    "E6": [["E6", "E7"], ["E6", "E1"], ["E6", "E3"]],
    "E8": [["E8", "E1"], ["E8", "E3"], ["E8", "E5"]],
}
# Vehicle type and its chance (in %)
VEHICLE_TYPES = [
    ("car", 55),
    ("motorcycle", 25),
    ("truck", 10),
    ("bus", 5),
    ("van", 5),
]

# xxxxxxxxxxxx Signal Settings xxxxxxxxxxxx
# Weight of each vehicle 
SECONDS_PER_VEHICLE = {
    "motorcycle": 0.5,
    "car": 1.0,
    "van": 1.5,
    "bus": 2.0,
    "truck": 3.0,
    "ambulance": 1.5,
    "firetruck": 1.5,
}

DEFAULT_SECONDS_PER_VEHICLE = 1.0
DETECTION_DISTANCE = 80.0 # Upto 80m from junction vehicle will be counted 
MIN_TIMER = 10 
MAX_TIMER = 40 
YELLOW_TIME = 3
ALL_RED_TIME = 2 
RESUME_IF_GREEN_SECONDS = 10 # This is for E.V. crossing 
assert MIN_TIMER > YELLOW_TIME

# xxxxxxxxxxxx Sound Settings xxxxxxxxxxxx
SOUND_ON = True 
SOUND_DIR = os.path.join(PROJECT_DIR , "sounds") #External folder 
CHECK_SOUND_EVERY_STEPS = 5
FULL_VOLUME_VEHICLES = 40
HUM_MAX_VOLUME = 0.5
HONK_AFTER_WAITING = 8
HONK_CHANCE = 0.3
HONK_GAP_SECONDS = 1.5
HONK_VOLUME = 0.6
SIREN_VOLUME = 0.7
FIRE_SIREN_VOLUME = 0.7

HORN_OF_VEHICLE = {
    "car": "horn_car",
    "van": "horn_car",
    "motorcycle": "horn_bike",
    "bus": "horn_bus",
    "truck": "horn_truck",
}

# xxxxxxxxxxxxxx Emergency Vehicle Settings xxxxxxxxxxxxx
AMBULANCE_ON =True
FIRETRUCK_ON =True
AMBULANCE_PAIR_CHANCE = 0.5 # 0.0 = never together, 1.0 = always one pair
AMBULANCE_START_FRACTION = 0.10
AMBULANCE_END_FRACTION = 0.90
EMERGENCY_PREFIXES = ("ambulance_", "firetruck_") # E.V.Id's
EMERGENCY_NAMES = {"ambulance": "AMBULANCE", "firetruck": "FIRE TRUCK"}
AMBULANCE_DETECTION_DISTANCE = 100.0 #Upto 100m the E.V. detected 
BLINK_SECONDS =0.5

# xxxxxxxxxxxxxxx Create Random Traffic xxxxxxxxxxxxxxx
# Decide random type of vehicle 
def pick_random_vehicle_type():
    weighted_list = []
    for vehicle_type, chance in VEHICLE_TYPES:
        weighted_list.extend([vehicle_type] * chance)
    return random.choice(weighted_list)

def add_emergency_vehicles(vehicle_list):
    fleet = []
    if AMBULANCE_ON:
        fleet += [("ambulance", edge) for edge in INCOMING_EDGES]
    if FIRETRUCK_ON:
        fleet += [("firetruck", edge) for edge in INCOMING_EDGES]
    if not fleet:
        return
    random.shuffle(fleet)

    groups = [[vehicle] for vehicle in fleet]
    if len(groups) >= 2 and random.random() < AMBULANCE_PAIR_CHANCE:
        first = groups[0][0]
        for strict in (True, False):
            partner = next((g for g in groups[1:]
                            if g[0][1] != first[1] and (not strict or g[0][0] != first[0])), None)
            if partner:
                groups.remove(partner)
                groups[0].append(partner[0])
                break
    random.shuffle(groups) # the pair can be early or late
    window_start = AMBULANCE_START_FRACTION * SIMULATION_TIME
    window_end = AMBULANCE_END_FRACTION * SIMULATION_TIME
    slot_width = (window_end - window_start) / len(groups)

    for slot_number, group in enumerate(groups):
        slot_centre = window_start + slot_width * (slot_number + 0.5)
        start_time = slot_centre + random.uniform(-0.25, 0.25) * slot_width
        for vehicle_type, edge in group:
            path = random.choice(VALID_ROUTES[edge])
            colour = "255,255,255" if vehicle_type == "ambulance" else "220,0,0"
            vehicle_list.append((start_time, f"{vehicle_type}_{edge}", vehicle_type, path, colour))

def create_random_traffic():
    print("Creating traffic...")
    routes = ET.Element("routes")
    ET.SubElement(routes, "vType", id="car", vClass="passenger", accel="2.6", decel="4.5", sigma="0.5", length="4.5", minGap="2.5", maxSpeed="13.89")
    ET.SubElement(routes, "vType", id="motorcycle", vClass="motorcycle", accel="3.0", decel="5.0", sigma="0.5", length="2.5", minGap="1.0", maxSpeed="16.67")
    ET.SubElement(routes, "vType", id="truck", vClass="truck", accel="1.0", decel="3.5", sigma="0.5", length="10.0", minGap="3.0", maxSpeed="11.11")
    ET.SubElement(routes, "vType", id="bus", vClass="bus", accel="1.2", decel="4.0", sigma="0.5", length="12.0", minGap="3.0", maxSpeed="12.5")
    ET.SubElement(routes, "vType", id="van", vClass="delivery", accel="2.0", decel="4.0", sigma="0.5", length="5.5", minGap="2.5", maxSpeed="13.89")
    ET.SubElement(routes, "vType", id="ambulance", vClass="emergency", guiShape="emergency", accel="5.0", decel="5.0", sigma="0.3", length="6.0", minGap="2.0", maxSpeed="20.67", color="255,255,255")
    ET.SubElement(routes, "vType", id="firetruck", vClass="emergency", guiShape="firebrigade", accel="4.5", decel="4.5", sigma="0.3", length="9.0", minGap="2.5", maxSpeed="20.0", color="220,0,0")

    vehicle_list = []
    for i in range(NUMBER_OF_VEHICLES):
        vehicle_id = f"vehicle_{i}"
        start_road = random.choice(INCOMING_EDGES)
        path = random.choice(VALID_ROUTES[start_road])
        vehicle_type = pick_random_vehicle_type()
        colour = f"{random.randint(30, 255)},{random.randint(30, 255)},{random.randint(30, 255)}"
        start_time = random.uniform(0, SIMULATION_TIME - 1)
        vehicle_list.append((start_time, vehicle_id, vehicle_type, path, colour))
    add_emergency_vehicles(vehicle_list)
    vehicle_list.sort(key=lambda item: item[0])     # earliest vehicle first
    for i, (start_time, vehicle_id, vehicle_type, path, colour) in enumerate(vehicle_list):
        route_id = f"route_{i}"
        ET.SubElement(routes, "route", id=route_id, edges=" ".join(path))
        ET.SubElement(
            routes, "vehicle",
            id=vehicle_id, type=vehicle_type, route=route_id,
            depart=f"{start_time:.2f}", departLane="random",
            departSpeed="random", color=colour,
        )
    tree = ET.ElementTree(routes)
    ET.indent(tree, space="    ")
    tree.write(ROUTE_FILE, encoding="UTF-8", xml_declaration=True)
    emergency_count = (4 if AMBULANCE_ON else 0) + (4 if FIRETRUCK_ON else 0)
    print(f"Created {NUMBER_OF_VEHICLES} vehicles + {emergency_count} emergency vehicles")
    print(f"Route file: {ROUTE_FILE}")

# xxxxxxxxxxxxx GUI Settings File xxxxxxxxxxxxxx
def write_gui_settings():
    """Creates the settings file for the SUMO window: text style, speed,
    camera position and the background image.
    The text background is transparent because each label has its own
    black panel (see SignalController)."""
    xml = f'''<viewsettings>
    <!-- Label text style: white text, transparent background -->
    <scheme name="real world">
        <pois poiType_show="1" poiType_size="90" poiType_color="255,255,255"
              poiType_bgColor="0,0,0,0" poiType_constantSize="1"
              poiName_show="0" poiText_show="0"/>
    </scheme>

    <!-- Speed of the simulation (ms per step) -->
    <delay value="{GUI_DELAY_MS}"/>

    <!-- Camera position -->
    <viewport x="{VIEW_X}" y="{VIEW_Y}" zoom="{VIEW_ZOOM}" angle="{VIEW_ANGLE}"/>

    <!-- Background aerial image -->
    <decal file="{BACKGROUND_IMAGE}" centerX="0" centerY="0"
           width="{IMAGE_WIDTH}" height="{IMAGE_HEIGHT}" rotation="0" layer="-1"/>
</viewsettings>
'''
    with open(GUI_SETTINGS_FILE, "w") as f:
        f.write(xml)

# xxxxxxxxxxxxxx Count Vehicles near the stop line xxxxxxxxxxxxxx
def count_vehicles_in_lane(edge_id):
    count_per_type = {}
    for vehicle_id in traci.edge.getLastStepVehicleIDs(edge_id):
        lane_id = traci.vehicle.getLaneID(vehicle_id)
        distance_to_stop_line =  traci.lane.getLength(lane_id) - traci.vehicle.getLanePosition(vehicle_id)
        if distance_to_stop_line <= DETECTION_DISTANCE : 
            vehicle_type = traci.vehicle.getTypeID(vehicle_id)
            count_per_type[vehicle_type] = count_per_type.get(vehicle_type, 0) + 1

    vehicle_count = sum(count_per_type.values())
    demand_second = sum(
        SECONDS_PER_VEHICLE.get(t,DEFAULT_SECONDS_PER_VEHICLE) * n
        for t , n in count_per_type.items()
    )
    return vehicle_count, demand_second, count_per_type

# xxxxxxxxxxxxxxx Calculate Timer xxxxxxxxxxxxxx
def calculate_timer(demand_seconds):
    total = math.ceil(demand_seconds)
    return max(MIN_TIMER, min(MAX_TIMER, total))

# xxxxxxxxxxxxxx Main If - else rules Controller xxxxxxxxxxxxxx

class SignalController:
    GREEN, YELLOW, ALL_RED = "GREEN", "YELLOW", "ALL_RED"
    def __init__(self):
        self.light_id, self.signals_of_lane, self.signal_count = self._find_traffic_light()
        self.label_ids = self._create_labels()
        self._last_shown = {}            # what each label shows now
        self.current_lane = 0            # position in INCOMING_EDGES (0 = Lane 1)
        self.phase = None                # GREEN, YELLOW or ALL_RED
        self.phase_end_time = 0.0        # when the current colour ends
        self.timer_end_time = 0.0        # when the timer reaches 0
        self.green_start_time = 0.0      # when the current green started
        self.pending_lane = 0            # lane that gets green after the next all-red
        self.fixed_timer = 0             # timer chosen at the start (does not change)
        self.fixed_count = 0             # vehicle count at the start (does not change)
        self.fixed_demand = 0.0
        # Emergency (ambulance / fire truck) mode
        self.emergency_active = False
        self.emergency_lane = None       # index in INCOMING_EDGES of the emergency lane
        self.ambulance_edge = {}         # emergency vehicle id -> incoming road it is crossing
        self._start_green(self.current_lane, traci.simulation.getTime())

    # ---------- set-up helpers ----------
    def _find_traffic_light(self):
        for light_id in traci.trafficlight.getIDList():
            signals = {edge: [] for edge in INCOMING_EDGES}
            links = traci.trafficlight.getControlledLinks(light_id)
            for index, link_group in enumerate(links):
                for in_lane, _out, _via in link_group:
                    edge = traci.lane.getEdgeID(in_lane)
                    if edge in signals and index not in signals[edge]:
                        signals[edge].append(index)
            if all(signals.values()):
                print(f"Controlling traffic light '{light_id}'")
                return light_id, signals, len(links)
        raise RuntimeError(
            "No traffic light controls edges " + ", ".join(INCOMING_EDGES) +
            ". Open the network in netedit and set the junction type to "
            "'traffic_light'."
        )

    def _label_position(self, edge_id):
        shape = traci.lane.getShape(edge_id + "_0")
        (x1, y1), (x2, y2) = shape[-2], shape[-1]
        length = math.hypot(x2 - x1, y2 - y1) or 1.0
        dx, dy = (x2 - x1) / length, (y2 - y1) / length
        return x2 - dx * 12 - dy * 15, y2 - dy * 12 + dx * 15 # 12m back and 15m from lane 

    def _rectangle_shape(self, x, y):
        w, h = PANEL_WIDTH / 2, PANEL_HEIGHT / 2
        return [(x - w, y - h), (x + w, y - h), (x + w, y + h), (x - w, y + h)]

    def _circle_shape(self, x, y, radius=CIRCLE_RADIUS):
        points = []
        for step in range(24):
            angle = 2 * math.pi * step / 24
            points.append((x + radius * math.cos(angle),
                           y + radius * math.sin(angle)))
        return points

    def _create_labels(self):
        label_ids = {}
        for edge in INCOMING_EDGES:
            x, y = self._label_position(edge)
            panel_id, circle_id, halo_id = f"panel_{edge}", f"circle_{edge}", f"halo_{edge}"
            count_id, timer_id = f"count_{edge}", f"timer_{edge}"
            traci.polygon.add(panel_id, self._rectangle_shape(x, y), COLOUR_PANEL, fill=True, layer=240) # Black panel 
            traci.polygon.add(halo_id, self._circle_shape(x, y, HALO_RADIUS), COLOUR_PANEL, fill=True, layer=243) # Halo circle 
            traci.polygon.add(circle_id, self._circle_shape(x, y), COLOUR_RED, fill=True, layer=245) # Circle
            traci.poi.add(count_id, x, y + TEXT_DISTANCE, COLOUR_TEXT, poiType="", layer=250, width=0.5, height=0.5) # count 
            traci.poi.add(timer_id, x, y - TEXT_DISTANCE, COLOUR_TEXT, poiType="", layer=250, width=0.5, height=0.5) # timer 
            label_ids[edge] = (count_id, timer_id, circle_id, halo_id) #entire label 
        return label_ids

    # ---------- light colour helpers ----------
    def _show_lane_colour(self, lane_index, colour):
        state = ["r"] * self.signal_count
        for i in self.signals_of_lane[INCOMING_EDGES[lane_index]]:
            state[i] = colour
        traci.trafficlight.setRedYellowGreenState(self.light_id, "".join(state))

    def _show_all_red(self):
        traci.trafficlight.setRedYellowGreenState(self.light_id, "r" * self.signal_count)

    # ---------- normal cycle ----------
    def _start_green(self, first_lane, now):
        """Starts green for first_lane. If that lane is EMPTY it is skipped
        (timer 0) and the next lane is tried, and so on."""
        n = len(INCOMING_EDGES)
        chosen, count, demand = first_lane, 0, 0.0
        for offset in range(n):
            lane = (first_lane + offset) % n
            c, d, _ = count_vehicles_in_lane(INCOMING_EDGES[lane])
            if c > 0:
                chosen, count, demand = lane, c, d
                break
            print(f"[t={now:6.1f}s] Lane {lane + 1} ({INCOMING_EDGES[lane]}) | "
                  f"no vehicles -> timer=0, skipped")
        # (if ALL lanes are empty, 'first_lane' gets a MIN_TIMER green so the cycle keeps going)

        edge = INCOMING_EDGES[chosen]
        # Count and timer are decided NOW and stay FIXED for this whole turn.
        self.fixed_count = count
        self.fixed_demand = demand
        self.fixed_timer = calculate_timer(demand)
        self.current_lane = chosen
        self.pending_lane = (chosen + 1) % n
        self.phase = self.GREEN
        self.green_start_time = now
        self.timer_end_time = now + self.fixed_timer
        # Green ends YELLOW_TIME seconds before the timer reaches 0
        self.phase_end_time = self.timer_end_time - YELLOW_TIME
        self._show_lane_colour(chosen, "G")
        print(f"[t={now:6.1f}s] Lane {chosen + 1} ({edge}) | "
              f"vehicles={count} demand={demand:.1f}s -> timer={self.fixed_timer}s "
              f"(green {self.fixed_timer - YELLOW_TIME}s + yellow {YELLOW_TIME}s)")

    def _go_to_next_phase(self, now):
        if self.phase == self.GREEN:              # only YELLOW_TIME seconds left
            self.phase = self.YELLOW
            self.phase_end_time = self.timer_end_time   # yellow lasts until timer = 0
            self._show_lane_colour(self.current_lane, "y")
        elif self.phase == self.YELLOW:           # timer reached 0
            self.phase = self.ALL_RED
            self.phase_end_time = now + ALL_RED_TIME
            self._show_all_red()
        else:
            self._start_green(self.pending_lane, now)

    # ---------- emergency (ambulance / fire truck) mode ----------
    def _find_ambulance_lane(self):
        candidates = {}                          # edge -> distance to stop line
        present = set()
        for vehicle_id in traci.vehicle.getIDList():
            if not vehicle_id.startswith(EMERGENCY_PREFIXES):
                continue
            present.add(vehicle_id)
            road = traci.vehicle.getRoadID(vehicle_id)
            if road in INCOMING_EDGES:
                lane_id = traci.vehicle.getLaneID(vehicle_id)
                distance = traci.lane.getLength(lane_id) - traci.vehicle.getLanePosition(vehicle_id)
                if distance <= AMBULANCE_DETECTION_DISTANCE:
                    self.ambulance_edge[vehicle_id] = road
                    candidates[road] = min(distance, candidates.get(road, 1e9))
            elif road.startswith(":") and vehicle_id in self.ambulance_edge:
                # inside the junction: keep the green until it is out
                edge = self.ambulance_edge[vehicle_id]
                candidates[edge] = min(0.0, candidates.get(edge, 1e9))
            else:
                self.ambulance_edge.pop(vehicle_id, None)    # it has passed

        for vehicle_id in list(self.ambulance_edge):
            if vehicle_id not in present:
                del self.ambulance_edge[vehicle_id]

        if not candidates:
            return None
        if self.emergency_lane is not None and INCOMING_EDGES[self.emergency_lane] in candidates:
            return self.emergency_lane           # keep serving the same vehicle
        nearest_edge = min(candidates, key=candidates.get)
        return INCOMING_EDGES.index(nearest_edge)

    def _emergency_name(self, lane_index):
        edge = INCOMING_EDGES[lane_index]
        kinds = {vid.split("_")[0] for vid, e in self.ambulance_edge.items() if e == edge}
        if len(kinds) == 1:
            return EMERGENCY_NAMES.get(kinds.pop(), "EMERGENCY")
        return "EMERGENCY"

    def _start_emergency(self, lane_index, now):
        if not self.emergency_active and self.phase == self.GREEN:
            served = now - self.green_start_time
            if served <= RESUME_IF_GREEN_SECONDS:
                self.pending_lane = self.current_lane      # barely started -> run it again later
                note = (f"Lane {self.current_lane + 1} had only {served:.1f}s green -> "
                        f"it will restart after the emergency")
            else:
                note = (f"Lane {self.current_lane + 1} had {served:.1f}s green -> "
                        f"cycle continues with Lane {self.pending_lane + 1} after the emergency")
            print(f"[t={now:6.1f}s] {note}")

        self.emergency_active = True
        self.emergency_lane = lane_index
        self._show_lane_colour(lane_index, "G")  # emergency lane green, others red
        print(f"[t={now:6.1f}s] EMERGENCY ({self._emergency_name(lane_index)}) on Lane {lane_index + 1} "
              f"({INCOMING_EDGES[lane_index]}) -> green for it, others blinking red")

    def _end_emergency(self, now):
        lane = self.emergency_lane
        n = len(INCOMING_EDGES)
        if self.pending_lane == lane:
            self.pending_lane = (lane + 1) % n
        print(f"[t={now:6.1f}s] Emergency vehicle passed Lane {lane + 1} -> YELLOW, then red, "
              f"then Lane {self.pending_lane + 1} continues the cycle")
        self.emergency_active = False
        self.emergency_lane = None
        # Emergency lane goes YELLOW first (not straight to red)
        self.current_lane = lane
        self.fixed_count, _d, _ = count_vehicles_in_lane(INCOMING_EDGES[lane])
        self.phase = self.YELLOW
        self.timer_end_time = now + YELLOW_TIME
        self.phase_end_time = self.timer_end_time
        self._show_lane_colour(lane, "y")

    # ---------- called after every simulation step ----------
    def update(self):
        now = traci.simulation.getTime()
        ambulance_lane = self._find_ambulance_lane()
        if ambulance_lane is not None:
            if not self.emergency_active or self.emergency_lane != ambulance_lane:
                self._start_emergency(ambulance_lane, now)
            self._update_emergency_labels(now)
            return
        if self.emergency_active:
            self._end_emergency(now)
        if now >= self.phase_end_time - 1e-9:
            self._go_to_next_phase(now)
        self._update_labels(now)

    def _update_emergency_labels(self, now):
        blink_on = int(now / BLINK_SECONDS) % 2 == 0
        for i, edge in enumerate(INCOMING_EDGES):
            count_id, timer_id, circle_id, halo_id = self.label_ids[edge]
            count, _demand, _ = count_vehicles_in_lane(edge)
            if i == self.emergency_lane:
                timer_text = self._emergency_name(self.emergency_lane)
                circle_colour, halo_colour = COLOUR_GREEN, COLOUR_HALO
            else:
                timer_text = "STOP"
                circle_colour = COLOUR_RED if blink_on else COLOUR_RED_DIM
                halo_colour = COLOUR_PANEL
            self._set_text(count_id, f"COUNT : {count}")
            self._set_text(timer_id, timer_text)
            self._set_circle_colour(circle_id, circle_colour)
            self._set_circle_colour(halo_id, halo_colour)

    def _update_labels(self, now):
        for i, edge in enumerate(INCOMING_EDGES):
            count_id, timer_id, circle_id, halo_id = self.label_ids[edge]
            if i == self.current_lane:
                count = self.fixed_count
                if self.phase == self.ALL_RED:
                    timer_text, circle_colour = "TIMER : 0", COLOUR_RED
                else:
                    seconds_left = max(0, math.ceil(self.timer_end_time - now - 1e-9))
                    timer_text = f"TIMER : {seconds_left}"    # one countdown for green + yellow
                    circle_colour = COLOUR_GREEN if self.phase == self.GREEN else COLOUR_YELLOW
            else:
                count, _demand, _ = count_vehicles_in_lane(edge)
                timer_text = "TIMER : 0" if count == 0 else "TIMER : --"
                circle_colour = COLOUR_RED
            self._set_text(count_id, f"COUNT : {count}")
            self._set_text(timer_id, timer_text)
            self._set_circle_colour(circle_id, circle_colour)
            self._set_circle_colour(halo_id, COLOUR_PANEL)         # no highlight in normal mode

    def _set_text(self, text_id, text):
        if self._last_shown.get(text_id) != text:
            traci.poi.setType(text_id, text)
            self._last_shown[text_id] = text

    def _set_circle_colour(self, circle_id, colour):
        if self._last_shown.get(circle_id) != colour:
            traci.polygon.setColor(circle_id, colour)
            self._last_shown[circle_id] = colour

# xxxxxxxxxxxxxx Traffic Sound xxxxxxxxxxxxx
class TrafficSound:
    SOUND_NAMES = ["traffic_hum", "horn_car", "horn_bike", "horn_bus", "horn_truck", "siren", "siren_fire"]
    def __init__(self):
        self.ready = False
        self.step_number = 0
        self.hum_volume = 0.0
        self.siren_volume = 0.0
        self.fire_siren_volume = 0.0
        self.last_honk_time = 0.0
        if not SOUND_ON:
            return
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.set_num_channels(16)
            self.sounds = {
                name: pygame.mixer.Sound(os.path.join(SOUND_DIR, name + ".wav"))
                for name in self.SOUND_NAMES
            }
            for name in ("traffic_hum", "siren", "siren_fire"):
                self.sounds[name].set_volume(0.0)
                self.sounds[name].play(loops=-1)
            self.pygame = pygame
            self.ready = True
            print("Sound is ON")
        except ImportError:
            print("Sound is OFF. To turn it on, run:  pip install pygame")
        except Exception as e:
            print("Sound is OFF:", e)

    def update(self):
        """Call this after every simulation step."""
        if not self.ready:
            return
        self.step_number += 1
        if self.step_number % CHECK_SOUND_EVERY_STEPS != 0:
            return

        moving_count = 0
        ambulance_count = 0
        fire_count = 0
        waiting_vehicles = []
        for vehicle_id in traci.vehicle.getIDList():
            vehicle_type = traci.vehicle.getTypeID(vehicle_id)
            if vehicle_type == "ambulance":
                ambulance_count += 1
            elif vehicle_type == "firetruck":
                fire_count += 1
            speed = traci.vehicle.getSpeed(vehicle_id)
            if speed > 0.5:
                moving_count += 1
            elif speed < 0.1 and traci.vehicle.getWaitingTime(vehicle_id) >= HONK_AFTER_WAITING:
                waiting_vehicles.append((vehicle_id, vehicle_type))

        # 1. Traffic hum: more moving vehicles = louder (changes smoothly)
        target = min(1.0, moving_count / FULL_VOLUME_VEHICLES) * HUM_MAX_VOLUME
        self.hum_volume += (target - self.hum_volume) * 0.2
        self.sounds["traffic_hum"].set_volume(self.hum_volume)

        # 2. Sirens: each plays while its vehicle type is in the simulation
        siren_target = SIREN_VOLUME if ambulance_count > 0 else 0.0
        self.siren_volume += (siren_target - self.siren_volume) * 0.3
        self.sounds["siren"].set_volume(self.siren_volume)

        fire_target = FIRE_SIREN_VOLUME if fire_count > 0 else 0.0
        self.fire_siren_volume += (fire_target - self.fire_siren_volume) * 0.3
        self.sounds["siren_fire"].set_volume(self.fire_siren_volume)

        # 3. Horn: a long-waiting vehicle may honk now and then
        if waiting_vehicles and random.random() < HONK_CHANCE:
            if time.time() - self.last_honk_time >= HONK_GAP_SECONDS:
                _, vehicle_type = random.choice(waiting_vehicles)
                horn = self.sounds[HORN_OF_VEHICLE.get(vehicle_type, "horn_car")]
                horn.set_volume(HONK_VOLUME)
                horn.play()
                self.last_honk_time = time.time()

    def stop(self):
        if self.ready:
            self.pygame.mixer.quit()

# xxxxxxxxxxxxxxx Start SUMO And Run xxxxxxxxxxxxxxx
def start_sumo():
    if not os.path.exists(SUMO_CONFIG):
        print("Error : Visuals.sumocfg not found...")
        print(SUMO_CONFIG)
        return False
    if "SUMO_HOME" not in os.environ:
        print("Error : SUMO_HOME is not set")
        return False
    program_name = "sumo-gui" if USE_GUI else "sumo"
    if os.name == "nt":
        program_name +=".exe"
    sumo_program = os.path.join(os.environ["SUMO_HOME"], "bin", program_name)

    if not os.path.exists(sumo_program):
        print(f"ERROR: {program_name} not found")
        print(sumo_program)
        return False

    print("Starting SUMO...")
    command = [sumo_program, "-c", SUMO_CONFIG, "--step-length", str(STEP_LENGTH)]
    if USE_GUI:
        write_gui_settings()
        command += ["--delay", str(GUI_DELAY_MS), "--gui-settings-file", GUI_SETTINGS_FILE]
    try:
        traci.start(command)
        return True
    except Exception as e:
        print("ERROR starting SUMO:")
        print(e)
        return False

def run_simulation():
    print("At Traffic Management System")
    create_random_traffic()
    if not start_sumo():
        return
    print("Simulation Started")
    sound = TrafficSound()
    try:
        controller = SignalController()
        while traci.simulation.getMinExpectedNumber()>0:
            traci.simulationStep()
            controller.update()
            sound.update()
    except RuntimeError as e:
        print("Error: ", e)
    finally:
        sound.stop()
        traci.close()
    print("Simulation finished...")
if __name__ == "__main__":
    run_simulation()

    




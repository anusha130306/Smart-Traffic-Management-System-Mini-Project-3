# BASELINE: static signals (fixed 30 s timer, one lane after another, no emergency priority)
import math
import os
import random
import struct
import time
import wave
import xml.etree.ElementTree as ET
import traci

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ROUTE_FILE = os.path.join(PROJECT_DIR, "Editfile.rou.xml")
SUMO_CONFIG = os.path.join(PROJECT_DIR, "Visuals.sumocfg")
GUI_SETTINGS_FILE = os.path.join(PROJECT_DIR, "gui_settings.xml")
BACKGROUND_IMAGE = os.path.join(PROJECT_DIR, "IsolationArielImage.png")

# Simulation
SIMULATION_TIME = 300
NUMBER_OF_VEHICLES = 300
RANDOM_SEED = 42               # use the same seed in the AI version (None = random)
STEP_LENGTH = 0.1
GUI_DELAY_MS = 1000
VIEW_X, VIEW_Y, VIEW_ZOOM, VIEW_ANGLE = 0, 0, 150, 0
IMAGE_WIDTH, IMAGE_HEIGHT = 210.12, 189.22
USE_GUI = os.environ.get("USE_GUI", "1") == "1"

# Fixed signal timing
FIXED_TIMER = 30               # seconds per lane (green + yellow)
YELLOW_TIME = 3
ALL_RED_TIME = 2

# Label look: black panel, light circle, timer text
TEXT_DISTANCE = 4.5
PANEL_WIDTH, PANEL_HEIGHT = 17.0, 9.0
CIRCLE_RADIUS = 1.6
COLOUR_RED = (220, 30, 30, 255)
COLOUR_GREEN = (0, 200, 0, 255)
COLOUR_YELLOW = (255, 200, 0, 255)
COLOUR_PANEL = (0, 0, 0, 255)
COLOUR_TEXT = (255, 255, 255, 255)

# Roads
INCOMING_EDGES = ["E2", "E4", "E6", "E8"]
VALID_ROUTES = {
    "E2": [["E2", "E3"], ["E2", "E5"], ["E2", "E7"]],
    "E4": [["E4", "E5"], ["E4", "E7"], ["E4", "E1"]],
    "E6": [["E6", "E7"], ["E6", "E1"], ["E6", "E3"]],
    "E8": [["E8", "E1"], ["E8", "E3"], ["E8", "E5"]],
}
VEHICLE_TYPES = [("car", 55), ("motorcycle", 25), ("truck", 10), ("bus", 5), ("van", 5)]

# Emergency vehicles (1 ambulance + 1 fire truck per lane, no priority here)
AMBULANCE_PAIR_CHANCE = 0.5
AMBULANCE_START_FRACTION = 0.10
AMBULANCE_END_FRACTION = 0.90

# Sound (needs: pip install pygame)
SOUND_ON = True
SOUND_DIR = os.path.join(PROJECT_DIR, "sounds")
CHECK_SOUND_EVERY_STEPS = 5
FULL_VOLUME_VEHICLES = 40
HUM_MAX_VOLUME = 0.5
HONK_AFTER_WAITING = 8
HONK_CHANCE = 0.3
HONK_GAP_SECONDS = 1.5
HONK_VOLUME = 0.6
SIREN_VOLUME = 0.7
FIRE_SIREN_VOLUME = 0.7
HORN_OF_VEHICLE = {"car": "horn_car", "van": "horn_car", "motorcycle": "horn_bike",
                   "bus": "horn_bus", "truck": "horn_truck"}

# ------------------------------------------------------------------ traffic
def add_emergency_vehicles(vehicle_list):
    fleet = [(kind, edge) for kind in ("ambulance", "firetruck") for edge in INCOMING_EDGES]
    random.shuffle(fleet)
    groups = [[v] for v in fleet]
    if random.random() < AMBULANCE_PAIR_CHANCE:
        first = groups[0][0]
        for strict in (True, False):
            partner = next((g for g in groups[1:]
                            if g[0][1] != first[1] and (not strict or g[0][0] != first[0])), None)
            if partner:
                groups.remove(partner)
                groups[0].append(partner[0])
                break
    random.shuffle(groups)
    start = AMBULANCE_START_FRACTION * SIMULATION_TIME
    slot = (AMBULANCE_END_FRACTION * SIMULATION_TIME - start) / len(groups)
    for n, group in enumerate(groups):
        t = start + slot * (n + 0.5) + random.uniform(-0.25, 0.25) * slot
        for kind, edge in group:
            colour = "255,255,255" if kind == "ambulance" else "220,0,0"
            vehicle_list.append((t, f"{kind}_{edge}", kind, random.choice(VALID_ROUTES[edge]), colour))

def create_random_traffic():
    if RANDOM_SEED is not None:
        random.seed(RANDOM_SEED)
    routes = ET.Element("routes")
    ET.SubElement(routes, "vType", id="car", vClass="passenger", accel="2.6", decel="4.5", sigma="0.5", length="4.5", minGap="2.5", maxSpeed="13.89")
    ET.SubElement(routes, "vType", id="motorcycle", vClass="motorcycle", accel="3.0", decel="5.0", sigma="0.5", length="2.5", minGap="1.0", maxSpeed="16.67")
    ET.SubElement(routes, "vType", id="truck", vClass="truck", accel="1.0", decel="3.5", sigma="0.5", length="10.0", minGap="3.0", maxSpeed="11.11")
    ET.SubElement(routes, "vType", id="bus", vClass="bus", accel="1.2", decel="4.0", sigma="0.5", length="12.0", minGap="3.0", maxSpeed="12.5")
    ET.SubElement(routes, "vType", id="van", vClass="delivery", accel="2.0", decel="4.0", sigma="0.5", length="5.5", minGap="2.5", maxSpeed="13.89")
    ET.SubElement(routes, "vType", id="ambulance", vClass="emergency", guiShape="emergency", accel="3.0", decel="5.0", sigma="0.3", length="6.0", minGap="2.0", maxSpeed="16.67", color="255,255,255")
    ET.SubElement(routes, "vType", id="firetruck", vClass="emergency", guiShape="firebrigade", accel="2.5", decel="4.5", sigma="0.3", length="9.0", minGap="2.5", maxSpeed="15.0", color="220,0,0")

    weighted = [t for t, chance in VEHICLE_TYPES for _ in range(chance)]
    vehicle_list = []
    for i in range(NUMBER_OF_VEHICLES):
        path = random.choice(VALID_ROUTES[random.choice(INCOMING_EDGES)])
        vehicle_type = random.choice(weighted)
        colour = f"{random.randint(30, 255)},{random.randint(30, 255)},{random.randint(30, 255)}"
        vehicle_list.append((random.uniform(0, SIMULATION_TIME - 1), f"vehicle_{i}", vehicle_type, path, colour))
    add_emergency_vehicles(vehicle_list)
    vehicle_list.sort(key=lambda item: item[0])
    for i, (t, vid, vtype, path, colour) in enumerate(vehicle_list):
        ET.SubElement(routes, "route", id=f"route_{i}", edges=" ".join(path))
        ET.SubElement(routes, "vehicle", id=vid, type=vtype, route=f"route_{i}", depart=f"{t:.2f}",
                      departLane="random", departSpeed="random", color=colour)
    tree = ET.ElementTree(routes)
    ET.indent(tree, space="    ")
    tree.write(ROUTE_FILE, encoding="UTF-8", xml_declaration=True)

# ------------------------------------------------------------------ gui
def write_gui_settings():
    xml = f'''<viewsettings>
    <scheme name="real world">
        <pois poiType_show="1" poiType_size="90" poiType_color="255,255,255"
              poiType_bgColor="0,0,0,0" poiType_constantSize="1"
              poiName_show="0" poiText_show="0"/>
    </scheme>
    <delay value="{GUI_DELAY_MS}"/>
    <viewport x="{VIEW_X}" y="{VIEW_Y}" zoom="{VIEW_ZOOM}" angle="{VIEW_ANGLE}"/>
    <decal file="{BACKGROUND_IMAGE}" centerX="0" centerY="0"
           width="{IMAGE_WIDTH}" height="{IMAGE_HEIGHT}" rotation="0" layer="-1"/>
</viewsettings>
'''
    with open(GUI_SETTINGS_FILE, "w") as f:
        f.write(xml)

# ------------------------------------------------------------------ fixed signal
class SignalController:
    """Lane 1 -> 2 -> 3 -> 4 -> 1 ... each: green, yellow (FIXED_TIMER total), then all-red."""
    def __init__(self):
        self.light_id, self.signals_of_lane, self.signal_count = self._find_traffic_light()
        self.labels = self._create_labels()
        self.shown = {}
        self.lane = 0
        self._start_green(0, traci.simulation.getTime())

    def _find_traffic_light(self):
        for light_id in traci.trafficlight.getIDList():
            signals = {edge: [] for edge in INCOMING_EDGES}
            for index, link_group in enumerate(traci.trafficlight.getControlledLinks(light_id)):
                for in_lane, _out, _via in link_group:
                    edge = traci.lane.getEdgeID(in_lane)
                    if edge in signals and index not in signals[edge]:
                        signals[edge].append(index)
            if all(signals.values()):
                return light_id, signals, len(traci.trafficlight.getControlledLinks(light_id))
        raise RuntimeError("No traffic light controls edges " + ", ".join(INCOMING_EDGES))

    def _create_labels(self):
        labels = {}
        w, h = PANEL_WIDTH / 2, PANEL_HEIGHT / 2
        for edge in INCOMING_EDGES:
            (x1, y1), (x2, y2) = traci.lane.getShape(edge + "_0")[-2:]
            length = math.hypot(x2 - x1, y2 - y1) or 1.0
            dx, dy = (x2 - x1) / length, (y2 - y1) / length
            x, y = x2 - dx * 10 - dy * 15, y2 - dy * 10 + dx * 15
            traci.polygon.add(f"panel_{edge}", [(x - w, y - h), (x + w, y - h), (x + w, y + h), (x - w, y + h)],
                              COLOUR_PANEL, fill=True, layer=240)
            circle = [(x + CIRCLE_RADIUS * math.cos(a * math.pi / 12), y + CIRCLE_RADIUS * math.sin(a * math.pi / 12))
                      for a in range(24)]
            traci.polygon.add(f"circle_{edge}", circle, COLOUR_RED, fill=True, layer=245)
            traci.poi.add(f"timer_{edge}", x, y - TEXT_DISTANCE, COLOUR_TEXT, poiType="", layer=250, width=0.5, height=0.5)
            labels[edge] = (f"timer_{edge}", f"circle_{edge}")
        return labels

    def _show_lane_colour(self, colour):
        state = ["r"] * self.signal_count
        for i in self.signals_of_lane[INCOMING_EDGES[self.lane]]:
            state[i] = colour
        traci.trafficlight.setRedYellowGreenState(self.light_id, "".join(state))

    def _start_green(self, lane, now):
        self.lane, self.phase = lane, "GREEN"
        self.timer_end = now + FIXED_TIMER
        self.phase_end = self.timer_end - YELLOW_TIME
        self._show_lane_colour("G")

    def update(self):
        now = traci.simulation.getTime()
        if now >= self.phase_end - 1e-9:
            if self.phase == "GREEN":
                self.phase, self.phase_end = "YELLOW", self.timer_end
                self._show_lane_colour("y")
            elif self.phase == "YELLOW":
                self.phase, self.phase_end = "ALL_RED", now + ALL_RED_TIME
                traci.trafficlight.setRedYellowGreenState(self.light_id, "r" * self.signal_count)
            else:
                self._start_green((self.lane + 1) % len(INCOMING_EDGES), now)
        for i, edge in enumerate(INCOMING_EDGES):
            timer_id, circle_id = self.labels[edge]
            if i != self.lane:
                text, colour = "TIMER : --", COLOUR_RED
            elif self.phase == "ALL_RED":
                text, colour = "TIMER : 0", COLOUR_RED
            else:
                text = f"TIMER : {max(0, math.ceil(self.timer_end - now - 1e-9))}"
                colour = COLOUR_GREEN if self.phase == "GREEN" else COLOUR_YELLOW
            if self.shown.get(timer_id) != text:
                traci.poi.setType(timer_id, text)
                self.shown[timer_id] = text
            if self.shown.get(circle_id) != colour:
                traci.polygon.setColor(circle_id, colour)
                self.shown[circle_id] = colour

# ------------------------------------------------------------------ sound
def save_tone(file_path, seconds, pitches, fade=0.03, wobble_hz=0):
    """Makes a simple .wav sound by mixing pitches (frequency in Hz, volume)."""
    rate = 22050
    total = int(rate * seconds)
    samples = []
    for n in range(total):
        t = n / rate
        value = sum(volume * math.sin(2 * math.pi * hz * t) for hz, volume in pitches)
        if wobble_hz:                                   # slow up-down wobble (engine feel)
            value *= 0.8 + 0.2 * math.sin(2 * math.pi * wobble_hz * t)
        # fade in and fade out so there is no "click" sound
        edge = min(t, seconds - t)
        if edge < fade:
            value *= edge / fade
        samples.append(int(max(-1.0, min(1.0, value)) * 32000))

    with wave.open(file_path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(b"".join(struct.pack("<h", s) for s in samples))

def save_siren(file_path, seconds=2.0, base_hz=900, sweep_hz=400):
    """Wailing siren: pitch rises and falls once per loop (loops seamlessly)."""
    rate = 22050
    samples = []
    for n in range(int(rate * seconds)):
        t = n / rate
        phase = 2 * math.pi * (base_hz * t + sweep_hz * seconds / (2 * math.pi) * (1 - math.cos(2 * math.pi * t / seconds)))
        samples.append(int(0.6 * math.sin(phase) * 32000))
    with wave.open(file_path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(b"".join(struct.pack("<h", s) for s in samples))

def create_sound_files():
    """Makes the sound files if they are missing.
    You can replace any of them with your own real .wav file
    (keep the same file name) inside the 'sounds' folder."""
    os.makedirs(SOUND_DIR, exist_ok=True)
    sounds = {
        # name         : (seconds, [(pitch Hz, volume), ...], wobble Hz)
        # hum is 2 seconds with whole-number pitches, so it loops smoothly
        "traffic_hum": (2.0, [(50, 0.5), (100, 0.3), (150, 0.15), (200, 0.08)], 6),
        "horn_car":    (0.5, [(400, 0.4), (500, 0.4), (800, 0.1), (1000, 0.1)], 0),
        "horn_bike":   (0.25, [(800, 0.45), (1000, 0.45), (1600, 0.1)], 0),
        "horn_bus":    (0.8, [(300, 0.4), (380, 0.4), (600, 0.1), (760, 0.1)], 0),
        "horn_truck":  (1.0, [(200, 0.4), (250, 0.4), (400, 0.1), (500, 0.1)], 0),
    }
    for name, (seconds, pitches, wobble) in sounds.items():
        path = os.path.join(SOUND_DIR, name + ".wav")
        if not os.path.exists(path):
            save_tone(path, seconds, pitches, wobble_hz=wobble)

    siren_path = os.path.join(SOUND_DIR, "siren.wav")
    if not os.path.exists(siren_path):
        save_siren(siren_path)

    # Fire truck siren: lower and slower than the ambulance siren
    fire_path = os.path.join(SOUND_DIR, "siren_fire.wav")
    if not os.path.exists(fire_path):
        save_siren(fire_path, seconds=3.0, base_hz=600, sweep_hz=250)

class TrafficSound:
    """Plays traffic sounds while the simulation runs:
         1. A traffic hum that gets louder when more vehicles are moving.
         2. Horns from vehicles that have been waiting for a long time.
         3. A siren while any ambulance is on the road.
         4. A different siren while any fire truck is on the road."""

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
        except ImportError:
            print("Sound is OFF. To turn it on, run:  pip install pygame")
            return
        try:
            create_sound_files()
            pygame.mixer.init(frequency=22050, size=-16, channels=1)
            pygame.mixer.set_num_channels(16)
            self.sounds = {}
            for name in ["traffic_hum", "horn_car", "horn_bike", "horn_bus", "horn_truck", "siren", "siren_fire"]:
                self.sounds[name] = pygame.mixer.Sound(os.path.join(SOUND_DIR, name + ".wav"))
            self.sounds["traffic_hum"].set_volume(0.0)
            self.sounds["traffic_hum"].play(loops=-1)    # keeps playing all the time
            self.sounds["siren"].set_volume(0.0)
            self.sounds["siren"].play(loops=-1)          # silent until an ambulance appears
            self.sounds["siren_fire"].set_volume(0.0)
            self.sounds["siren_fire"].play(loops=-1)     # silent until a fire truck appears
            self.pygame = pygame
            self.ready = True
            print("Sound is ON")
        except Exception as e:
            print("Sound is OFF (could not start audio):", e)

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
                waiting_vehicles.append(vehicle_id)

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
                vehicle_id = random.choice(waiting_vehicles)
                vehicle_type = traci.vehicle.getTypeID(vehicle_id)
                horn_name = HORN_OF_VEHICLE.get(vehicle_type, "horn_car")
                horn = self.sounds[horn_name]
                horn.set_volume(HONK_VOLUME)
                horn.play()
                self.last_honk_time = time.time()

    def stop(self):
        if self.ready:
            self.pygame.mixer.quit()

# ------------------------------------------------------------------ run
def start_sumo():
    if "SUMO_HOME" not in os.environ:
        print("ERROR: SUMO_HOME is not set")
        return False
    program = "sumo-gui" if USE_GUI else "sumo"
    if os.name == "nt":
        program += ".exe"
    path = os.path.join(os.environ["SUMO_HOME"], "bin", program)
    command = [path, "-c", SUMO_CONFIG, "--step-length", str(STEP_LENGTH)]
    if USE_GUI:
        write_gui_settings()
        command += ["--delay", str(GUI_DELAY_MS), "--gui-settings-file", GUI_SETTINGS_FILE]
    try:
        traci.start(command)
        return True
    except Exception as e:
        print("ERROR starting SUMO:", e)
        return False

def run_simulation():
    create_random_traffic()
    if not start_sumo():
        return
    sound = TrafficSound()
    try:
        controller = SignalController()
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            controller.update()
            sound.update()
    except RuntimeError as e:
        print("ERROR:", e)
    finally:
        sound.stop()
        traci.close()

if __name__ == "__main__":
    run_simulation()
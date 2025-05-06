from Sensors.LeakPort import LeakPort
import Resources.Settings as Settings
from State.States import States
import Helpers.DeviceNames as DeviceNames
from Buzzers.Buzzers import Buzzers
from Logging.AppLogger import AppLogger
import Helpers.DeviceStates as DeviceStates
from LCD.Display import Display
from Valves.WaterLineValves import WaterLineValves

class LeakSensors:

    _zones = None

    def __init__(self,  states:States, display: Display, water_line_valves: WaterLineValves):
        self.states = states
        self.display = display
        self.water_line_valves = water_line_valves
        self.logger = AppLogger()
        self.buzzers = Buzzers()
        self.zone_1_leak = LeakPort(DeviceNames.ZONE_1_LEAK_SENSORS_KEY, Settings.LEAK_ZONE1_PIN, self._zone_1_leak_handler)
        self.zone_2_leak = LeakPort(DeviceNames.ZONE_2_LEAK_SENSORS_KEY, Settings.LEAK_ZONE2_PIN, self._zone_2_leak_handler)
        self._zone_1_leak_triggered = self.zone_1_leak.is_detected_leak()
        self._zone_2_leak_triggered = self.zone_2_leak.is_detected_leak()
        self._update_leaks_sensor_state()

    def is_detected_leaks(self) -> bool:
        return self._zone_1_leak_triggered == True or self._zone_2_leak_triggered == True
    
    def start(self):
        self.zone_1_leak.start()
        self.zone_2_leak.start()
        self.logger.info(f"LEAK SENSORS: Leak sensor [{self.zone_1_leak.name} and {self.zone_2_leak.name}] has start monitoring")
        
    def stop(self):
        self.zone_1_leak.stop()
        self.zone_2_leak.stop()
        self.logger.info("LEAK SENSORS: Leak sensor monitoring has stoped")

    # MARK: HELPERS
    def _update_leaks_sensor_state(self):
        zone1 = self.zone_1_leak.get_leak_state()
        zone2 = self.zone_2_leak.get_leak_state()
       
        self.states.update_leak_sensor_state(self.zone_1_leak.name, zone1)
        self.states.update_leak_sensor_state(self.zone_2_leak.name, zone2)
        self.logger.debug(f"LEAK SENSOR: Update leak sensor state: ZONE 1: {zone1}, ZONE 2: {zone2}")

    def _zone_1_leak_handler(self, state:str) -> None:
        self._zone_1_leak_triggered = True if state == DeviceStates.LEAK else False
        if self._zone_1_leak_triggered:
            self.logger.debug(f"LEAK SENSOR: Detected leak in ZONE 1")
            self.states.update_leak_sensor_state(self.zone_1_leak.name, state)
            self._make_akarm()
            
    def _zone_2_leak_handler(self, state:str) -> None:
        self._zone_2_leak_triggered = True if state == DeviceStates.LEAK else False
        if self._zone_2_leak_triggered:
            self.logger.debug(f"LEAK SENSOR: Detected leak in ZONE 2")
            self.states.update_leak_sensor_state(self.zone_2_leak.name, state)
            self._make_akarm()

    def _make_akarm(self):
        zones = self._get_alarm_zones()
        if zones != self._zones:
            if self._zones is None:
                self.water_line_valves.leak_detected()
                self.buzzers.alarm.play_alarm()
            self._zones = zones
            self.display.show_alarm("!! LEAK DETECTED !!", zones)

    def _get_alarm_zones(self):
        if self._zone_1_leak_triggered and self._zone_2_leak_triggered:
            return "Zone 1 & Zone 2"
        elif self._zone_1_leak_triggered:
            return "Zone 1"
        elif self._zone_2_leak_triggered:
            return "Zone 2"
        else:
            return None
        
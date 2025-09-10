import Resources.Settings as Settings
from Valves.WaterLineValves import WaterLineValves
from Buttons.ValveButtonsHandler import ValveButtonsHandler
from Sensors.LeakSensors import LeakSensors
from LCD.Display import Display

class ColdHotValveButtons:

    def __init__(self, valve: WaterLineValves, leak_sensors: LeakSensors, display = None):
        self.cold_water_buttons = ValveButtonsHandler(valve.cold_water_valve, Settings.VCOB_PIN, Settings.VCCB_PIN, leak_sensors, display)
        self.hot_water_buttons = ValveButtonsHandler(valve.hot_water_valve, Settings.VHOB_PIN, Settings.VHCB_PIN, leak_sensors, display)

    def start(self):
        self.cold_water_buttons.start()
        self.hot_water_buttons.start()

    def stop(self):
        self.cold_water_buttons.stop()
        self.hot_water_buttons.stop()
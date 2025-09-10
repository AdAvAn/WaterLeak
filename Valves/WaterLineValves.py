from State.States import States
from LCD.Display import Display
from Valves.ColdWaterValve import ColdWaterValve
from Valves.HotWaterValve import HotWaterValve

class WaterLineValves:
    def __init__(self, state: States, display = None):
        self.hot_water_valve = HotWaterValve(state, display)
        self.cold_water_valve = ColdWaterValve(state, display)

    def leak_detected(self):
        self.hot_water_valve.leak_detected()
        self.cold_water_valve.leak_detected()

    def fircse_stop(self):
        self.hot_water_valve.force_stop()
        self.cold_water_valve.force_stop()

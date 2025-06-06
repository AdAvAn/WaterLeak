from State.States import States
import Helpers.DeviceNames as DeviceNames
import Helpers.LcdCustomSymbols as Symbols
import Resources.Settings as Settings
from Valves.ValvesInterface import ValvesInterface  
from LCD.Display import Display

class ColdWaterValve(ValvesInterface):
    
    def __init__(self, state: States, display:Display):
        self.display = display
        super().__init__(
            device_name = DeviceNames.COLD_WATER_VALVE_KEY, 
            open_pin = Settings.OPEN_COLD_W_PIN, 
            close_pin = Settings.CLOSE_COLD_W_PIN, 
            feedback_pin = Settings.ERROR_COLD_W_PIN, 
            state = state
        )

    def open_progress(self, device_name, progress):
        title = f"{Symbols.VALVE}|Cold opening..."
        unic_device_name = "opening_" + device_name
        self.display.show_progress(title, unic_device_name , progress)

    def close_progress(self, device_name, progress):
        title = f"{Symbols.VALVE}|Cold closing..."
        unic_device_name = "closing_" + device_name
        self.display.show_progress(title, unic_device_name, progress)

from Buttons.ButtonPort import ButtonPort
from Buzzers.Buzzers import Buzzers
from Logging.AppLogger import AppLogger
from Valves.ValvesInterface import ValvesInterface  
from Sensors.LeakSensors import LeakSensors
from LCD.Display import Display

class ValveButtonsHandler:
    
    def __init__(self, valve: ValvesInterface, open_pin: int, close_pin: int, leak_sensors: LeakSensors, display:Display):
        self.buzzer = Buzzers()
        self.logger = AppLogger()
        self.open_button = ButtonPort(open_pin, self._open_callback)
        self.close_button = ButtonPort(close_pin, self._close_callback)
        self.leak_sensors = leak_sensors
        self.valve = valve
        self.display = display
        
    def start(self):
        self.open_button.start()
        self.close_button.start()

    def stop(self):
        self.open_button.stop()
        self.close_button.stop()

    def _open_callback(self, event: str) -> None:
        if event == ButtonPort.SHORT_EVENT_ID:
            self._short_open_handler()
        elif event == ButtonPort.LONG_EVENT_ID:
            self._long_open_handler()

    def _close_callback(self, event: str) -> None:
        if event == ButtonPort.SHORT_EVENT_ID:
            self._short_close_handler()
        elif event == ButtonPort.LONG_EVENT_ID:
            self._long_close_handler()

    def _short_open_handler(self) -> None:
        if self.leak_sensors.is_detected_leaks():
            self.leak_sensors.clear()
            self.logger.info(f"BUTTONS: Action Forbidden becose leak detected")
        else:
            if self.valve.is_in_progress():
                self.valve.force_stop()

            try:
                self.valve.open()
                self.buzzer.control.play_confirm() 
                self.logger.info(f"BUTTONS: Start manual opening valve: {self.valve.device_name}")
            except Exception as e:
                self.buzzer.control.play_error() 
                self.logger.error(f"BUTTONS: FAIELD: {e}")
            

    def _short_close_handler(self) -> None:
        if self.leak_sensors.is_detected_leaks():
            self.leak_sensors.clear()
            self.logger.info(f"BUTTONS: Action forbidden because Leak Detected")
        else:
            if self.valve.is_in_progress():
                self.valve.force_stop()
                
            try:
                self.valve.close()
                self.buzzer.control.play_confirm() 
                self.logger.info(f"BUTTONS: Start manual closing valve:  {self.valve.device_name}")
            except Exception as e:
                self.buzzer.control.play_error() 
                self.logger.error(f"BUTTONS: FAIELD: {e}")  
            
    def _long_open_handler(self) -> None:
        pass  

    def _long_close_handler(self) -> None:
        pass  



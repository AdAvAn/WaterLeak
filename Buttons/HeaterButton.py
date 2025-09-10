import Resources.Settings as Settings
from Buttons.ButtonPort import ButtonPort
from Buzzers.Buzzers import Buzzers
from Logging.AppLogger import AppLogger
from Heater.HeaterPowerSwith import HeaterPowerSwith
from State.States import States

class HeaterButton:
    
    def __init__(self, states: States, leak_sensors=None):
        self.buzzer = Buzzers()
        self.logger = AppLogger()
        self._port = ButtonPort(Settings.HOCB_PIN, self.callback)
        self.heater = HeaterPowerSwith(states)
        self.leak_sensors = leak_sensors  # Add reference to leak sensors
        
    def start(self):
        self._port.start()

    def stop(self):
        self._port.stop()

    def _is_alarm_active(self) -> bool:
        """Check if alarm mode is currently active"""
        if self.leak_sensors is None:
            return False
        return (self.leak_sensors.is_detected_leaks() and 
                not self.leak_sensors._alarm_acknowledged)

    def callback(self, event: str) -> None:
        if event == ButtonPort.SHORT_EVENT_ID:
            self._short_handler()
        elif event == ButtonPort.LONG_EVENT_ID:
            self._long_handler()

    def _short_handler(self) -> None:
        # If alarm is active, any button press clears the alarm
        if self._is_alarm_active():
            self.logger.info(f"BUTTONS: Alarm mode active - clearing alarm instead of toggling heater")
            if self.leak_sensors:
                self.leak_sensors.clear()
                return

        # Normal operation
        self.buzzer.control.play_confirm()
        self.heater.toggle()
        self.logger.info(f"BUTTONS: Heater toggled")

    def _long_handler(self) -> None:
        # If alarm is active, any button press clears the alarm
        if self._is_alarm_active():
            self.logger.info(f"BUTTONS: Alarm mode active - clearing alarm instead of long heater action")
            if self.leak_sensors:
                self.leak_sensors.clear()
                return
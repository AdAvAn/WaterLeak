import Helpers.DeviceNames as DeviceNames
import Helpers.DeviceStates as DeviceStates
from machine import Pin
from Logging.AppLogger import AppLogger
import Resources.Settings as Settings
from State.States import States

class HeaterPowerSwith:
   
    def __init__(self, states:States):
        self._pin = Pin(Settings.POWER_HEATER_PIN, mode=Pin.OUT)
        self._device_name = DeviceNames.HEATER_POWER_SWITH_KEY
        self._logger = AppLogger()
        self._states = states   
        self._restore_state() 

    def is_on(self) -> bool:
        return self._pin.value() == 1

    def toggle(self):
        if self._pin.value() == 0:
            self.power_on()
            self._states.update_heater_state(self._device_name, DeviceStates.ON)
        else:
            self.power_off()
            self._states.update_heater_state(self._device_name, DeviceStates.OFF)

    def power_on(self):
        self._pin.high()

    def power_off(self):
        self._pin.low()

    def _restore_state(self):
        last_atate = self._states.get_heater_state(self._device_name)
        if last_atate: 
            if last_atate == DeviceStates.ON:
                self.power_on()
            elif last_atate == DeviceStates.OFF:
                self.power_off()


import Helpers.DeviceNames as DeviceNames
from RTC.DsRTC import DsRTC

# Abstract base class for all sensors
class SensorState:
    
    def __init__(self, device_name):
        self._device_name = device_name
        self._observers = []
        self._ds_rtc = DsRTC()
        self._state = None
        self._preview_state = None
        self._last_changed = None

    # MARK: Setter
    def add_observer(self, observer_fn) -> None:
        self._observers.append(observer_fn)

    def set_state(self, new_value, can_notify:bool) -> None:
        raise NotImplementedError("Subclass must implement abstract method set_state")
    
    def set_preview_state(self, preview_value) -> None:
         self._preview_state = preview_value
    
    def set_new_state(self, new_value) -> None:
         self._state = new_value
         self._last_changed = self._ds_rtc.get_datetime_iso8601()

    def set_last_changed(self, time) -> None:
        self.last_changed = time

         
    # MARK: GETTER
    def get_device_name(self) ->str:
        return self._device_name

    def get_state(self):
        return self._state
    
    def get_preview_state(self):
        return self._preview_state
    
    def get_last_changed(self):
        return self._last_changed

    # MARK: Helpers
    def _notify_observers(self, new_state) -> None:
        for observer_fn in self._observers:
            observer_fn(new_state)

    def get_data(self):
        return {
            DeviceNames.STATE_KEY: self.get_state(),
            DeviceNames.PREVIEW_STATE_KEY: self.get_preview_state(),
            DeviceNames.LAST_CHANGED_KEY: self.get_last_changed(),
        }
from State.SensorState import SensorState

class TemperatureSensorState(SensorState):
   
    def __init__(self, device_name):
        super().__init__(device_name)

    def set_state(self, new_value, can_notify:bool) -> None:
        current = self.get_state()
        if new_value != current:
            self.set_preview_state(current)
            self.set_new_state(new_value)
            if can_notify:
                self._notify_observers(new_value)

import Helpers.DeviceStates as DeviceStates
from State.States import States

class ValvesInterface:
    
    def __init__(self, device_name, open_pin, close_pin, feedback_pin, state: States):
        from .Valve.OpenValve import OpenValve
        from .Valve.CloseValve import CloseValve
        self.state = state
        self.device_name = device_name
        self.open_valve = OpenValve(self.device_name, open_pin, state)
        self.close_valve = CloseValve(self.device_name, close_pin, state)
        # self.feedback = ValvesFeedback(feedback_pin, self.valves_error_handler)
        self.open_valve.add_progress_observers(self.open_progress)
        self.close_valve.add_progress_observers(self.close_progress)
        
    def is_in_progress(self) -> bool:
        return self.open_valve.is_active() or self.close_valve.is_active()

    def is_open(self) -> bool:
        return self.state.get_valve_state(self.device_name) == DeviceStates.OPENED

    def is_close(self) -> bool:
        return self.state.get_valve_state(self.device_name) == DeviceStates.CLOSED
    
    def open(self):
        if self.close_valve.is_active():
            raise ValueError("VALVES: The current state of the open valve does not allow the task to be completed")
        self.open_valve.start(width_progress = True)

    def close(self):
        if self.open_valve.is_active():
            raise ValueError("VALVES: The current state of the open valve does not allow the task to be completed")
        self.close_valve.start(width_progress = True)

    def leak_detected(self):
        from Logging.AppLogger import AppLogger
        self.force_stop()
        self.close_valve.start(width_progress = False)
        self.logger = AppLogger()
        self.logger.debug("VALVES: Activated emergency valve closure")

    def force_stop(self):
        self.open_valve.stop()
        self.close_valve.stop()

    # """Returns the reason why stub is being used"""
    #     self.logger.critical(f"An error was detected when working with the valve  '{self.valve_type}': Overload, short circuit, or overheating. Turn off the valve.")
    #     self.state.update_valve_state(self.valve_type, ValveState.ERROR)
    #     self.open_valve.stop()
    #     self.close_valve.stop()

    def open_progress(self, device_name, progress):
        raise NotImplementedError("VALVES: Subclass must implement abstract method open_progress")

    def close_progress(self, device_name, progress):
        raise NotImplementedError("VALVES: Subclass must implement abstract method close_progress")


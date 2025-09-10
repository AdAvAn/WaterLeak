import uasyncio as asyncio
from machine import Pin
from State.States import States
from Logging.AppLogger import AppLogger
import Resources.Settings as Settings

class ValvePort:

    _task = None 

    def __init__(self, device_name: str, pin_id:int, state:States):
        self.pin = Pin(pin_id, Pin.OUT)
        self.device_name = device_name
        self.state = state
        self.operation_time_left: int = 0 
        self.operating_time  = Settings.VALVES_OPERATION_TIME
        self.progress_observers = [] 
        self.logger = AppLogger()

    def start(self, width_progress:bool):
        self._task = asyncio.create_task(self._operating_valve(width_progress))
    
    def add_progress_observers(self, observer_fn):
        self.progress_observers.append(observer_fn)

    def stop(self):
        if self._task is not None:
            try:
                self._task.cancel() 
                self.logger.info(f"VALVE: Task for valve '{self.device_name}' canceled")
            except Exception as e:
                self.logger.error(f"VALVE: Error canceling task for valve '{self.device_name}': {e}")
        self._task = None
        self.stop_valve()

    def clear_task(self):
        self._task = None

    def get_progress(self) -> int:
        return self.operation_time_left
    
    def step_of_progress(self) -> None:
        self.operation_time_left -= 1

    def reset_progress(self) -> None:
        self.operation_time_left = Settings.VALVES_OPERATION_TIME

    def _stop_task(self) -> None:
        if self._task != None:
            self._task.cancel() # type: ignore
            self._task = None
            self.logger.info(f"VALVE: Task for work width valve: '{self.device_name}' in stoped")
        
    def stop_valve(self) -> None:
        self.pin.low() 
    
    def start_valve(self) -> None:
        self.pin.high() 

    def is_active(self) -> bool:
        return self.pin.value() == 1
    
    async def _operating_valve(self, width_progress:bool) -> None:
        raise NotImplementedError("Subclass must implement abstract method set_state")

    def notify_progress_observers(self):
        progress = self.get_progress()
        for observer_fn in self.progress_observers:
            progress_float = (1 - progress / self.operating_time)
            observer_fn(self.device_name, progress_float)


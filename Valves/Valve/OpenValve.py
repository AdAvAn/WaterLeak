import uasyncio as asyncio
import Helpers.DeviceStates as DeviceStates
from State.States import States
from .ValvePort import ValvePort

class OpenValve(ValvePort):

    def __init__(self, device_name: str, pin_id:int, state:States):
        super().__init__(device_name, pin_id, state)

    async def _operating_valve(self, width_progress:bool) -> None:
        self.state.update_valve_state(self.device_name, DeviceStates.OPENING)
        self.reset_progress()
        self.start_valve()
        self.logger.debug(f"VALVE: Strt opening valve '{self.device_name}', {self.operation_time_left} sec remaining")
        
        while self.get_progress() > 0:
            self.step_of_progress()
            if self.get_progress() == 0:
                self.state.update_valve_state(self.device_name, DeviceStates.OPENED)
            if width_progress:
                self.notify_progress_observers()
            await asyncio.sleep(1)
        
        self.logger.debug(f"VALVE: Finish opening valve '{self.device_name}'")
        self.stop_valve()
        self.clear_task()

    
    
   
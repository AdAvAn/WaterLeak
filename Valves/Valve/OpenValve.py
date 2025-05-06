import uasyncio as asyncio
import Helpers.DeviceStates as DeviceStates
from State.States import States
from .ValvePort import ValvePort

import uasyncio as asyncio
import Helpers.DeviceStates as DeviceStates
from State.States import States
from .ValvePort import ValvePort

class OpenValve(ValvePort):

    def __init__(self, device_name: str, pin_id:int, state:States):
        super().__init__(device_name, pin_id, state)

    async def _operating_valve(self, width_progress:bool) -> None:
        try:
            self.state.update_valve_state(self.device_name, DeviceStates.OPENING)
            self.reset_progress()
            self.start_valve()
            self.logger.debug(f"VALVE: Start opening valve '{self.device_name}', {self.operation_time_left} sec remaining")
            
            while self.get_progress() > 0:
                self.step_of_progress()
                if width_progress:
                    self.notify_progress_observers()
                await asyncio.sleep(1)
                
                # If the task is cancelled, we terminate the work gracefully
                if self._task is None:
                    self.logger.debug(f"VALVE: Opening task for valve '{self.device_name}' was canceled")
                    break
            
            # Only if the timer has reached zero and the task has not been cancelled, we change the status
            if self.get_progress() <= 0 and self._task is not None:
                self.state.update_valve_state(self.device_name, DeviceStates.OPENED)
                self.logger.debug(f"VALVE: Finished opening valve '{self.device_name}'")
            
            self.stop_valve()
            self.clear_task()
            
        except Exception as e:
            self.logger.error(f"VALVE: Error during opening valve '{self.device_name}': {e}")
            self.stop_valve()
            self.clear_task()
            self.state.update_valve_state(self.device_name, DeviceStates.ERROR)

    
    
   
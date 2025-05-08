from machine import Pin
import Helpers.DeviceStates as DeviceStates
import uasyncio as asyncio

class LeakPort:
    def __init__(self, name: str, pin_id: int, handler) -> None:
        self.pin: Pin = Pin(pin_id, Pin.IN)
        self.name = name
        self.handler = handler
        self._task = None

    def stop(self) -> None:
       if self._task is not None:
            self._task = None

    def start(self) -> None:
       if self._task is None:
            self._task = asyncio.create_task(self._monitor_leak())

    def get_leak_state(self) -> str:
        return DeviceStates.LEAK if self.is_detected_leak() else DeviceStates.NO_LEAK

    def is_detected_leak(self) -> bool:
        return self.pin.value() == 0
    
    def leak_handler(self) -> None:
        self.handler(self.get_leak_state())

    async def _monitor_leak(self):
        while self._task is not None:
            self.leak_handler()
            await asyncio.sleep(5)
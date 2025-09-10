from machine import Pin
import Helpers.DeviceStates as DeviceStates
import uasyncio as asyncio

class LeakPort:
    def __init__(self, name: str, pin_id: int, handler) -> None:
        self.pin: Pin = Pin(pin_id, Pin.IN, Pin.PULL_UP)  # Added pull-up for better reliability
        self.name = name
        self.handler = handler
        self._task = None
        self._last_state = None  # Track last reported state to avoid duplicate calls

    def stop(self) -> None:
       if self._task is not None:
            self._task = None

    def start(self) -> None:
       if self._task is None:
            self._task = asyncio.create_task(self._monitor_leak())

    def get_leak_state(self) -> str:
        return DeviceStates.LEAK if self.is_detected_leak() else DeviceStates.NO_LEAK

    def is_detected_leak(self) -> bool:
        # Check pin state multiple times for debouncing
        readings = []
        for _ in range(3):
            readings.append(self.pin.value() == 0)
        
        # Return True only if at least 2 out of 3 readings indicate leak
        return sum(readings) >= 2
    
    def leak_handler(self) -> None:
        current_state = self.get_leak_state()
        
        # Only call handler if state actually changed
        if current_state != self._last_state:
            self._last_state = current_state
            self.handler(current_state)

    async def _monitor_leak(self):
        # Initialize last state
        self._last_state = self.get_leak_state()
        
        while self._task is not None:
            self.leak_handler()
            await asyncio.sleep(1)  # Check every second for better responsiveness
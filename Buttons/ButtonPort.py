from machine import Pin
import uasyncio as asyncio
import time


class ButtonPort:

    _PIN_SCAN_DELAY_MS = 10
    _PIN_DEBOUNCE_MS = 50
    _LONG_TIMEOUT_MS = 5000

    SHORT_EVENT_ID = "short"
    LONG_EVENT_ID = "long"

    def __init__(self, pin, callback):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.callback = callback
        self._task = None
        self._press_time = None

    def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self._monitor_button())

    def stop(self):
        if self._task:
            self._task = None

    async def _monitor_button(self):
        while self._task is not None:
            await asyncio.sleep_ms(self._PIN_SCAN_DELAY_MS)
            pin_state = self.pin.value()
            current_time = time.ticks_ms()

            if pin_state == 0:
                if self._press_time is None:
                    await asyncio.sleep_ms(self._PIN_DEBOUNCE_MS)
                    if self.pin.value() == 0:
                        self._press_time = current_time
            else:
                if self._press_time is not None:
                    press_duration = time.ticks_diff(current_time, self._press_time)
                    self._press_time = None
                    if press_duration >= self._LONG_TIMEOUT_MS:
                        self.callback(self.LONG_EVENT_ID)
                    else:
                        self.callback(self.SHORT_EVENT_ID)

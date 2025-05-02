from machine import Pin
import uasyncio as asyncio
import Resources.Settings as Settings
from Logging.AppLogger import AppLogger

class AlarmBuzzer:

    _SHORT_BUZZ: float = 0.2
    _LONG_BUZZ: float = 0.5

    def __init__(self):
        self._pin = Pin(Settings.BUZZ_ALARM_PIN, Pin.OUT)
        self._logger = AppLogger()
        self._task = None

    # MARK: Public
    def play_alarm(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._start_alarm())

    def off(self) -> None:
        if self._task is not None:
            self._task.cancel() # type: ignore
            self._task = None
            self._pin.value(0)

    # MARK: Helpers
    async def _start_alarm(self) -> None:
        while self._task is not None:
            await self._short_buz()
            await asyncio.sleep(0.2)
            await self._short_buz()
            await asyncio.sleep(0.2)
            await self._short_buz()
            await asyncio.sleep(0.2)
            await self._long_buz()
            await asyncio.sleep(3)

    async def _long_buz(self) -> None:
        self._pin.value(1)
        await asyncio.sleep(self._LONG_BUZZ)
        self._pin.value(0)

    async def _short_buz(self) -> None:
        self._pin.value(1)
        await asyncio.sleep(self._SHORT_BUZZ)
        self._pin.value(0)

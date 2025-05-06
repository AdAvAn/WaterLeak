from machine import Pin, PWM
import uasyncio as asyncio
import Resources.Settings as Settings
from Logging.AppLogger import AppLogger

class ControlBuzzer:

    do5=523
    dod5=554
    re5=587
    red5=622
    mi5=659
    fa5=698
    fad5=739
    sol5=784
    sold5=830
    la5=880
    lad5=932
    si5=987

    def __init__(self):
        self.appLogger = AppLogger()
        self.pin = PWM(Pin(Settings.BUZZ_CONTROL_PIN, Pin.OUT))
        self._task = None
        
    # MARK: Public
    def off(self) -> None:
        self._stop_task()
        self.pin.duty_u16(0)
 
    def play_started_app(self) -> None:
        self.off()
        self._task = asyncio.create_task(self._start_tone())

    def play_confirm(self) -> None:
        self.off()
        self._task = asyncio.create_task(self._confirm_tone())

    def play_done(self) -> None:
        self.off()
        self._task = asyncio.create_task(self._done_tone())

    def play_error(self) -> None:
        self.off()
        self._task = asyncio.create_task(self._error_tone())

    # MARK: Helpers
    def _stop_task(self) -> None:
        if self._task is not None:
            self._task.cancel() # type: ignore
            self._task = None
       
    async def _start_tone(self):
        await self._play_tone(self.do5, 0.2)  #  (C)
        await self._play_tone(self.mi5, 0.2)  #  (E)
        await self._play_tone(self.sol5, 0.2)  #  (G)

    async def _error_tone(self):
        await self._play_tone(self.la5, 0.2)  #  (A)
        await asyncio.sleep(0.2)
        await self._play_tone(self.la5, 0.2)  #  (A)

    async def _confirm_tone(self):
        await self._play_tone(self.la5, 0.2)  #  (A)

    async def _done_tone(self):
        await self._play_tone(self.lad5, 0.5) 

    async def _play_tone(self, frequency, duration):
        self.pin.freq(frequency)
        self.pin.duty_u16(int(65536*0.1))
        await asyncio.sleep(duration)
        self.pin.duty_u16(0)


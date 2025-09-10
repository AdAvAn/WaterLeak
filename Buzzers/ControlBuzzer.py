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
            try:
                if not self._task.done():  # Проверяем, что задача еще выполняется
                    self._task.cancel()
                self.appLogger.debug("CONTROL_BUZZER: Task stopped")
            except Exception as e:
                self.appLogger.error(f"CONTROL_BUZZER: Error stopping task: {e}")
            finally:
                self._task = None
       
    async def _start_tone(self):
        try:
            await self._play_tone(self.do5, 0.2)  # (C)
            await self._play_tone(self.mi5, 0.2)  # (E)
            await self._play_tone(self.sol5, 0.2)  # (G)
        except asyncio.CancelledError:
            self.appLogger.debug("CONTROL_BUZZER: Start tone cancelled")
        except Exception as e:
            self.appLogger.error(f"CONTROL_BUZZER: Error in start tone: {e}")
        finally:
            self.pin.duty_u16(0)

    async def _error_tone(self):
        try:
            await self._play_tone(self.la5, 0.2)  # (A)
            await asyncio.sleep(0.2)
            await self._play_tone(self.la5, 0.2)  # (A)
        except asyncio.CancelledError:
            self.appLogger.debug("CONTROL_BUZZER: Error tone cancelled")
        except Exception as e:
            self.appLogger.error(f"CONTROL_BUZZER: Error in error tone: {e}")
        finally:
            self.pin.duty_u16(0)

    async def _confirm_tone(self):
        try:
            await self._play_tone(self.la5, 0.2)  # (A)
        except asyncio.CancelledError:
            self.appLogger.debug("CONTROL_BUZZER: Confirm tone cancelled")
        except Exception as e:
            self.appLogger.error(f"CONTROL_BUZZER: Error in confirm tone: {e}")
        finally:
            self.pin.duty_u16(0)

    async def _done_tone(self):
        try:
            await self._play_tone(self.lad5, 0.5) 
        except asyncio.CancelledError:
            self.appLogger.debug("CONTROL_BUZZER: Done tone cancelled")
        except Exception as e:
            self.appLogger.error(f"CONTROL_BUZZER: Error in done tone: {e}")
        finally:
            self.pin.duty_u16(0)

    async def _play_tone(self, frequency, duration):
        try:
            self.pin.freq(frequency)
            self.pin.duty_u16(int(65536*0.1))
            await asyncio.sleep(duration)
            self.pin.duty_u16(0)
        except Exception as e:
            self.appLogger.error(f"CONTROL_BUZZER: Error playing tone: {e}")
            self.pin.duty_u16(0)  # Ensure buzzer is off on error
        
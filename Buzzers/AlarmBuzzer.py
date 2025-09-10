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
        # Stop any existing alarm first
        if self._task is not None:
            self.off()
            
        self._logger.info("ALARM_BUZZER: Starting alarm sequence")
        self._task = asyncio.create_task(self._start_alarm())

    def play_test_beep(self) -> None:
        """Play a short test beep to verify alarm buzzer is working"""
        if self._task is not None:
            self.off()
            
        self._logger.info("ALARM_BUZZER: Playing test beep")
        self._task = asyncio.create_task(self._test_beep())

    def off(self) -> None:
        if self._task is not None:
            try:
                if not self._task.done():  # Check if task is still running
                    self._task.cancel()
                self._logger.info("ALARM_BUZZER: Alarm stopped")
            except Exception as e:
                self._logger.error(f"ALARM_BUZZER: Error stopping task: {e}")
            finally:
                self._task = None
                self._pin.value(0)  # Ensure pin is off

    # MARK: Helpers
    async def _start_alarm(self) -> None:
        try:
            self._logger.info("ALARM_BUZZER: Alarm sequence started")
            cycle_count = 0
            while self._task is not None:
                cycle_count += 1
                
                # Three short beeps
                await self._short_buz()
                await asyncio.sleep(0.2)
                await self._short_buz()
                await asyncio.sleep(0.2)
                await self._short_buz()
                await asyncio.sleep(0.2)
                
                # One long beep
                await self._long_buz()
                
                # Wait before next cycle
                await asyncio.sleep(3)
                
        except asyncio.CancelledError:
            self._logger.info("ALARM_BUZZER: Alarm cancelled")
        except Exception as e:
            self._logger.error(f"ALARM_BUZZER: Error in alarm: {e}")
        finally:
            self._pin.value(0)
            self._logger.info("ALARM_BUZZER: Alarm sequence ended")

    async def _test_beep(self) -> None:
        """Play a short test beep"""
        try:
            self._logger.debug("ALARM_BUZZER: Playing first test beep")
            await self._short_buz()
            await asyncio.sleep(0.1)
            await self._short_buz()
        except asyncio.CancelledError:
            self._logger.debug("ALARM_BUZZER: Test beep cancelled")
        except Exception as e:
            self._logger.error(f"ALARM_BUZZER: Error in test beep: {e}")
        finally:
            self._pin.value(0)
            self._task = None

    async def _long_buz(self) -> None:
        try:
            self._pin.value(1)
            await asyncio.sleep(self._LONG_BUZZ)
            self._pin.value(0)
        except Exception as e:
            self._logger.error(f"ALARM_BUZZER: Error in long buzz: {e}")
            self._pin.value(0)

    async def _short_buz(self) -> None:
        try:
            self._pin.value(1)
            await asyncio.sleep(self._SHORT_BUZZ)
            self._pin.value(0)
        except Exception as e:
            self._logger.error(f"ALARM_BUZZER: Error in short buzz: {e}")
            self._pin.value(0)
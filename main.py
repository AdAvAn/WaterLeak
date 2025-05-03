import uasyncio as asyncio
from Buzzers import Buzzers
from Logging.AppLogger import AppLogger
from Buzzers.Buzzers import Buzzers
from Buttons.ColdHotValveButtons import ColdHotValveButtons
from State.States import States
from Valves.WaterLineValves import WaterLineValves
from LCD.Display import Display
from Sensors.TempSensors import TempSensors
from Sensors.LeakSensors import LeakSensors
from RTC.DsRTC import DsRTC
from Buttons.HeaterButton import HeaterButton
from Heater.HeaterPowerSwith import HeaterPowerSwith
import sys

class Main:
    def __init__(self):
        # Create Realtime module 
        self.ds_rtc = DsRTC() 
        
        # Create State module 
        self.states = States()
        
        # Create Logger module 
        self.logger = AppLogger()
        
        # Create Buzzers module 
        self.buzzers = Buzzers()
        
        # Create Display module 
        self.display = Display(self.states)
        
        # Create Valve
        self.water_line_valves = WaterLineValves(self.states, self.display)

        # Leak sensors
        self.leak_sensors = LeakSensors(self.states, self.display, self.water_line_valves)

        try:
            # Temp sensors - this could fail
            self.temp_sensors = TempSensors(self.states)
            self._temp_sensors_initialized = True
        except Exception as e:
            self._temp_sensors_initialized = False
            self.logger.error(f"Failed to initialize temperature sensors: {e}")
            self._handle_initialization_error("TEMP-ERR", str(e))
            # We don't re-raise the exception, allowing the system to continue with limited functionality

        try:
            # Create Buttons
            self.valve_buttons = ColdHotValveButtons(self.water_line_valves, self.leak_sensors, self.display)
            self._valve_buttons_initialized = True
        except Exception as e:
            self._valve_buttons_initialized = False
            self.logger.error(f"Failed to initialize valve buttons: {e}")
            self._handle_initialization_error("BTN-ERR", str(e))

        try:
            # Heater Switch 
            self.heater_swith = HeaterPowerSwith(self.states)
            # Heater button
            self.heater_button = HeaterButton(self.states)
            self._heater_initialized = True
        except Exception as e:
            self._heater_initialized = False
            self.logger.error(f"Failed to initialize heater controls: {e}")
            self._handle_initialization_error("HEAT-ERR", str(e))

    def _handle_initialization_error(self, code, text):
        # Play error sound if buzzers are available
        if hasattr(self, 'buzzers') and self.buzzers:
            self.buzzers.control.play_error()

        # Show error on display if it's available
        if hasattr(self, 'display') and self.display:
            self.display.show_error_screen(code, text)
        
    async def startOperating(self):
        await self.ds_rtc.update_time()
        await asyncio.sleep(2)
        self.leak_sensors.start()
        
        # Start only initialized components
        if hasattr(self, '_temp_sensors_initialized') and self._temp_sensors_initialized:
            self.temp_sensors.start()
            

        await asyncio.sleep(2)
        
        if hasattr(self, '_valve_buttons_initialized') and self._valve_buttons_initialized:
            self.valve_buttons.start()
            
        if hasattr(self, '_heater_initialized') and self._heater_initialized:
            self.heater_button.start()
            
        self.display.show_default_screens()
        self.display.start()

        # Only play startup sound if no leaks detected and leak sensors are working
        if not self.leak_sensors.is_detected_leaks():
            self.buzzers.control.play_started_app()

    async def run(self): 
        await self.startOperating()
        self.logger.info(f"Leak controller Started. Date: {self.ds_rtc.get_datetime_ddmmyy()}")
        while True:
            await asyncio.sleep(0.5)
          
    def cleanup(self):
        # Safely stop all components that might have been initialized
        if hasattr(self, '_temp_sensors_initialized') and self._temp_sensors_initialized:
            self.temp_sensors.stop()
            
        self.buzzers.control.off()
        self.leak_sensors.stop()
            
        if hasattr(self, '_valve_buttons_initialized') and self._valve_buttons_initialized:
            self.valve_buttons.stop()
            
        self.water_line_valves.fircse_stop()
        self.display.lcd.set_brightness(15)
        self.logger.warning(f"Leak controller stopped. Date: {self.ds_rtc.get_datetime_ddmmyy()}")

# Create an instance of the Main class and run it
if __name__ == "__main__":
    main = Main()
    try:
        asyncio.run(main.run())  # Start the async loop
    except KeyboardInterrupt:
        main.cleanup()
    except Exception as e:
        if hasattr(main, 'logger'):
            main.logger.critical(f"Fatal error: {e}")
        if hasattr(main, 'buzzers'):
            main.buzzers.control.play_error()
        if hasattr(main, 'display'):
            main.display.show_error_screen("SYS-ERR", str(e))
        sys.print_exception(e)  # Print full exception details
        # Clean up resources before exiting
        if hasattr(main, 'cleanup'):
            main.cleanup()
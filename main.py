import gc
import uasyncio as asyncio
from Logging.AppLogger import AppLogger
import sys

class Main:
    def __init__(self):
        self.logger = AppLogger()
        self.logger.info("Main: Initializing core components...")
    
        self._initializeBase()
        self._initializeOther()

    def _initializeBase(self):
            
            try:
                # State Machine
                from State.States import States
                self.states = States()
                gc.collect()
            except Exception as e:
                self.logger.error(f"Main: Failed to initialize State Machine: {e}")

            try:
                # Buzzers
                from Buzzers.Buzzers import Buzzers
                self.buzzers = Buzzers()
                gc.collect()
            except Exception as e:
                self.logger.error(f"Main: Failed to initialize Buzzers: {e}")

            try:
                # Display
                from LCD.Display import Display
                self.display = Display(self.states)
                gc.collect()
            except Exception as e:
                self.logger.error(f"Main: Failed to initialize Display: {e}")
                self._handle_initialization_error("Display Error", "Chek Display!")    
            
            try:
                # WiFi
                from Helpers.WiFiManager import WiFiManager
                self.wifiManager = WiFiManager()
                gc.collect()
            except Exception as e:
                self.logger.error(f"Main: Failed to initialize WiFi: {e}")
                self._handle_initialization_error("WiFi Error", "Chek SSID&Pass!")
            
            try:
                # DsRTC
                from RTC.DsRTC import DsRTC
                self.ds_rtc = DsRTC()
                gc.collect()
            except Exception as e:
                self.logger.error(f"Main: Failed to initialize Time chip (DsRTC): {e}")

              
    def _initializeOther(self):
        
        try:
            # Temp sensors
            from Sensors.TempSensors import TempSensors
            self.temp_sensors = TempSensors(self.states)
            gc.collect()
        except Exception as e:
            self.temp_sensors = None
            self.logger.error(f"Main: Failed to initialize temperature sensors: {e}")
            self._handle_initialization_error("Temp Sensor Err", "Chek Sensor!")

        try:
            # Valves
            from Valves.WaterLineValves import WaterLineValves
            self.water_line_valves = WaterLineValves(self.states, self.display)
            gc.collect()
        except Exception as e:
            self.logger.error(f"Main: Failed to initialize Valves: {e}")
            self._handle_initialization_error("ValvesD Err", "Chek Valves!")        

        try:
             # Heater Power Swith
            from Heater.HeaterPowerSwith import HeaterPowerSwith
            self.heater_swith = HeaterPowerSwith(self.states)
            gc.collect()
        except Exception as e:
            self.logger.error(f"Main: Failed to initialize Heater Power: {e}")
            self._handle_initialization_error("Err Hea.Power", "Chek!")           

        try:
            # Leak Sensors
            from Sensors.LeakSensors import LeakSensors
            self.leak_sensors = LeakSensors(self.states, self.display, self.water_line_valves, self.heater_swith)
            gc.collect()
        except Exception as e:
            self.logger.error(f"Main: Failed to initialize Leak Sensors: {e}")
            self._handle_initialization_error("Leak Err", "Chek Sensors!")    
    
        try:
             # Valve control buttons
            from Buttons.ColdHotValveButtons import ColdHotValveButtons
            self.valve_buttons = ColdHotValveButtons(self.water_line_valves, self.leak_sensors, self.display)
            gc.collect()
        except Exception as e:
            self.logger.error(f"Main: Failed to initialize Valves: {e}")
            self._handle_initialization_error("ValvesB Err", "Chek Valves!")     

        try:
            # Heater control Button
            from Buttons.HeaterButton import HeaterButton
            self.heater_button = HeaterButton(self.states)
            gc.collect()
        except Exception as e:
            self.logger.error(f"Main: Failed to initialize Heater Buttons: {e}")
            self._handle_initialization_error("Err Hea.PoButt", "Chek!")                
      

        self._web_server = None
        self._web_server_initialized = False

    def _handle_initialization_error(self, code, text):
        if self.buzzers != None:
            self.buzzers.control.play_error()
        if self.display != None and code != None:
            self.display.show_error_screen(code, text)
        
    async def startOperating(self):
        # Connect to WiFi
        self.logger.info("Main: Connecting to WiFi...")
        await self.wifiManager.connect_wifi()
        
        # Update time
        self.logger.info("Main: Updating time...")
        await self.ds_rtc.update_time()
        await asyncio.sleep(2)
        
        # Launch leak sensors
        self.logger.info("Main: Starting leak sensors...")
        self.leak_sensors.start()
        
        # Launch temperature sensors if initialized
        if self.temp_sensors:
            self.logger.info("Main: Starting temperature sensors...")
            self.temp_sensors.start()
            await asyncio.sleep(2)
            
        # Launch the valve control buttons if initialized
        self.valve_buttons.start()
            
        # Launch the heater control button if initialized
        self.logger.info("Main: Starting heater control button...")
        self.heater_button.start()
            
        # Turn on the display
        self.logger.info("Main: Starting display...")

        self.display.start()
        self.display.show_carusel()

        # Initialize and start the web server only if WiFi is connected
        if self.wifiManager.is_wifi_connected():
            try:
                self.logger.info("Main: Starting web server...")
                import WebServer.SimpleServer as WebServer
        
                self._web_server = WebServer.SimpleServer(
                    states=self.states,
                    valves=self.water_line_valves,
                    leak_sensors=self.leak_sensors,
                    heater_switch=self.heater_swith
                )
                
                gc.collect()
                
                self._web_server.start()
            except Exception as e:
                self.logger.error(f"Main: Failed to initialize web server: {e}")
                self._handle_initialization_error("WiFi", "Chek SSID&Pass!")

        # Sound signal at start-up if there are no leaks
        if not self.leak_sensors.is_detected_leaks():
            self.buzzers.control.play_started_app()

    def cleanup(self):
        # Safely stop all components that might have been initialized
        if self.temp_sensors:
            self.temp_sensors.stop()
        self.buzzers.control.off()
        self.leak_sensors.stop()
        self.valve_buttons.stop()
        self.water_line_valves.fircse_stop()
        self.display.lcd.set_brightness(15)
        self.logger.warning(f"Main: Leak controller stopped. Date: {self.ds_rtc.get_datetime_ddmmyy()}")

    async def run(self): 
        await self.startOperating() # type: ignore
        self.logger.info(f"Leak controller Started. Date: {self.ds_rtc.get_datetime_ddmmyy()}")
        
        tasks = []
        tasks.append(asyncio.create_task(self._main_loop()))
        if self._web_server != None:
            tasks.append(asyncio.create_task(self._web_server.run()))
        await asyncio.gather(*tasks)
    
    async def _main_loop(self):
        while True:
            await asyncio.sleep(0.5)
            # Periodically call the garbage collector
            if gc.mem_free() < 10000:  # If free memory is less than 10KB
                gc.collect()
        

# Create an instance of the Main class and run it
if __name__ == "__main__":
    main = Main()
    try:
        asyncio.run(main.run())  # Start the async loop
    except KeyboardInterrupt:
        main.cleanup()
    except Exception as e:
        sys.print_exception(e)  # Print full exception details
        if hasattr(main, 'logger'):
            main.logger.critical(f"Fatal error: {e}")
        if hasattr(main, 'buzzers'):
            main.buzzers.control.play_error()
        if hasattr(main, 'display'):
            main.display.show_error_screen("SYS-ERR", str(e))
        if hasattr(main, 'cleanup'):
            main.cleanup()
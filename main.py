import gc
import uasyncio as asyncio
from Logging.AppLogger import AppLogger
import sys
import time

class Main:
    def __init__(self):
        self.logger = AppLogger()
        self.logger.info("Main: Initializing core components...")
    
        self._initializeBase()
        self._initializeOther()

    def _initializeBase(self):
        try:
            # State Machine
            self._update_init_status("Init states...")
            from State.States import States
            self.states = States()
            gc.collect()
        except Exception as e:
            self.logger.error(f"Main: Failed to initialize State Machine: {e}")

        try:
            # Buzzers
            self._update_init_status("Init buzzers...")
            from Buzzers.Buzzers import Buzzers
            self.buzzers = Buzzers()
            gc.collect()
        except Exception as e:
            self.logger.error(f"Main: Failed to initialize Buzzers: {e}")

        try:
            # Display
            self._update_init_status("Init display...")
            from LCD.Display import Display
            self.display = Display(self.states)
            gc.collect()
        except Exception as e:
            self.display = None
            self.logger.error(f"Main: Failed to initialize Display: {e}")
            self._handle_initialization_error("Display Error", "Check Display!")    
        
        try:
            # WiFi
            self._update_init_status("Init WiFi...")
            from Helpers.WiFiManager import WiFiManager
            self.wifiManager = WiFiManager()
            gc.collect()
        except Exception as e:
            self.logger.error(f"Main: Failed to initialize WiFi: {e}")
            self._handle_initialization_error("WiFi Init Err", "Check WiFi module!")
        
        try:
            # DsRTC
            self._update_init_status("Init RTC...")
            from RTC.DsRTC import DsRTC
            self.ds_rtc = DsRTC()
            gc.collect()
        except Exception as e:
            self.logger.error(f"Main: Failed to initialize Time chip (DsRTC): {e}")

    def _initializeOther(self):
        try:
            # Temp sensors
            self._update_init_status("Init temp sens...")
            from Sensors.TempSensors import TempSensors
            self.temp_sensors = TempSensors(self.states)
            gc.collect()
            self.logger.info("Main: Temperature sensors initialized")
        except Exception as e:
            self.temp_sensors = None
            self.logger.error(f"Main: Failed to initialize temperature sensors: {e}")
            self._handle_initialization_error("Temp Sensor Err", "Check Sensors!")

        try:
            # Valves
            self._update_init_status("Init valves...")
            from Valves.WaterLineValves import WaterLineValves
            self.water_line_valves = WaterLineValves(self.states, self.display)
            gc.collect()
        except Exception as e:
            self.logger.error(f"Main: Failed to initialize Valves: {e}")
            self._handle_initialization_error("ValvesD Err", "Check Valves!")        

        try:
             # Heater Power Switch
            self._update_init_status("Init heater...")
            from Heater.HeaterPowerSwith import HeaterPowerSwith
            self.heater_swith = HeaterPowerSwith(self.states)
            gc.collect()
        except Exception as e:
            self.logger.error(f"Main: Failed to initialize Heater Power: {e}")
            self._handle_initialization_error("Err Hea.Power", "Check!")           

        try:
            # Leak Sensors
            self._update_init_status("Init leak sens...")
            from Sensors.LeakSensors import LeakSensors
            self.leak_sensors = LeakSensors(self.states, self.water_line_valves, self.heater_swith, self.display)
            gc.collect()
        except Exception as e:
            self.logger.error(f"Main: Failed to initialize Leak Sensors: {e}")
            self._handle_initialization_error("Leak Err", "Check Sensors!")    
    
        try:
             # Valve control buttons
            self._update_init_status("Init buttons...")
            from Buttons.ColdHotValveButtons import ColdHotValveButtons
            self.valve_buttons = ColdHotValveButtons(self.water_line_valves, self.leak_sensors, self.display)
            gc.collect()
        except Exception as e:
            self.logger.error(f"Main: Failed to initialize Valve Buttons: {e}")
            self._handle_initialization_error("ValvesB Err", "Check Buttons!")     

        try:
            # Heater control Button
            self._update_init_status("Init htr button...")
            from Buttons.HeaterButton import HeaterButton
            self.heater_button = HeaterButton(self.states)
            gc.collect()
        except Exception as e:
            self.logger.error(f"Main: Failed to initialize Heater Buttons: {e}")
            self._handle_initialization_error("Err Hea.Button", "Check!")                
      
        self._web_server = None
        self._web_server_initialized = False
        self._update_init_status("Init completed!")

    def _update_init_status(self, status: str):
        """Update initialization status on display if available"""
        if hasattr(self, 'display') and self.display:
            self.display.update_initialization_status(status)

    def _handle_initialization_error(self, code, text):
        if hasattr(self, 'buzzers') and self.buzzers is not None:
            self.buzzers.control.play_error()
        if hasattr(self, 'display') and self.display is not None and code is not None:
            self.display.show_error_screen(code, text)
        else:
            self.logger.error(f"Display Error: {code} - {text}")
        
    async def startOperating(self):
        # Connect to WiFi
        self._update_init_status("Connecting WiFi...")
        self.logger.info("Main: Connecting to WiFi...")
        await self.wifiManager.connect_wifi()
        
        # Update time
        self._update_init_status("Updating time...")
        self.logger.info("Main: Updating time...")
        await self.ds_rtc.update_time()
        await asyncio.sleep(1)
        
        # Launch leak sensors
        self._update_init_status("Start leak sens...")
        self.logger.info("Main: Starting leak sensors...")
        if hasattr(self, 'leak_sensors'):
            self.leak_sensors.start()
            # Give leak sensors time to stabilize and handle startup leaks
            await asyncio.sleep(3)
        
        # Launch temperature sensors if initialized
        if hasattr(self, 'temp_sensors') and self.temp_sensors:
            self._update_init_status("Start temp sens...")
            self.logger.info("Main: Starting temperature sensors...")
            self.temp_sensors.start()
            await asyncio.sleep(1)
            
        # Launch the valve control buttons if initialized
        if hasattr(self, 'valve_buttons'):
            self._update_init_status("Start buttons...")
            self.valve_buttons.start()
            
        # Launch the heater control button if initialized
        if hasattr(self, 'heater_button'):
            self._update_init_status("Start htr btn...")
            self.logger.info("Main: Starting heater control button...")
            self.heater_button.start()
            
        # Initialize and start the web server only if WiFi is connected
        if self.wifiManager.is_wifi_connected():
            try:
                self._update_init_status("Start web srv...")
                self.logger.info("Main: Starting web server...")
                import WebServer.SimpleServer as WebServer
        
                self._web_server = WebServer.SimpleServer(
                    states=self.states,
                    valves=self.water_line_valves,
                    leak_sensors=self.leak_sensors,
                    heater_switch=self.heater_swith
                )
                
                gc.collect()
                
                if self._web_server.start():
                    self.logger.info("Main: Web server started successfully")
                else:
                    self.logger.error("Main: Web server failed to start")
                    
            except Exception as e:
                self.logger.error(f"Main: Failed to initialize web server: {e}")
                self._handle_initialization_error("WebServer Err", "Check server code!")
        else:
            self.logger.warning("Main: WiFi not connected, skipping web server")

        # Turn on the display ONLY if it was initialized successfully
        if hasattr(self, 'display') and self.display:
            self._update_init_status("Start display...")
            self.logger.info("Main: Starting display...")
            self.display.start()
            await asyncio.sleep(1)  # Give time to see the final status
            self.display.show_carusel()
        else:
            self.logger.warning("Main: Display not available, continuing without display")

        # Check if there are any leaks detected during startup
        leaks_detected_at_startup = (hasattr(self, 'leak_sensors') and 
                                    self.leak_sensors and 
                                    self.leak_sensors.is_detected_leaks())

        if leaks_detected_at_startup:
            self.logger.critical("Main: LEAKS DETECTED AT STARTUP - Skipping startup sounds due to emergency condition")
        else:
            # Sound signal at start-up if there are no leaks
            # Test alarm buzzer first (short beep)
            self.logger.info("Main: Testing alarm buzzer...")
            self.buzzers.alarm.play_test_beep()
            await asyncio.sleep(1)  # Wait for test beep to complete
            
            # Then play startup melody
            self.logger.info("Main: Playing startup melody...")
            self.buzzers.control.play_started_app()

    async def cleanup(self):
        """Enhanced cleanup with proper state saving"""
        self.logger.info("Main: Starting cleanup process...")
        
        # Force save all pending state changes before shutdown
        if hasattr(self, 'states') and self.states:
            try:
                self.logger.info("Main: Forcing save of pending state changes...")
                await self.states.cleanup()
            except Exception as e:
                self.logger.error(f"Main: Failed to save states during cleanup: {e}")
        
        # Safely stop all components that might have been initialized
        if hasattr(self, 'temp_sensors') and self.temp_sensors:
            self.temp_sensors.stop()
        if hasattr(self, 'buzzers'):
            self.buzzers.control.off()
        if hasattr(self, 'leak_sensors'):
            self.leak_sensors.stop()
        if hasattr(self, 'valve_buttons'):
            self.valve_buttons.stop()
        if hasattr(self, 'heater_button'):
            self.heater_button.stop()
        if hasattr(self, 'water_line_valves'):
            self.water_line_valves.fircse_stop()
        
        if hasattr(self, 'display') and self.display:
            self.display.lcd.set_brightness(15)
        
        self.logger.warning(f"Main: Leak controller stopped. Date: {self.ds_rtc.get_datetime_ddmmyy()}")

    async def run(self):
        await self.startOperating()
        self.logger.info(f"Leak controller Started. Date: {self.ds_rtc.get_datetime_ddmmyy()}")
        
        # Create tasks with error handling
        tasks = []
        
        # Main loop with auto-restart
        tasks.append(asyncio.create_task(self._robust_main_loop()))
        
        # Web server with auto-restart
        if hasattr(self, '_web_server') and self._web_server:
            tasks.append(asyncio.create_task(self._robust_web_server()))
        
        # Monitoring WiFi connection
        tasks.append(asyncio.create_task(self._wifi_monitor()))
        
        # Watchdog for memory monitoring
        tasks.append(asyncio.create_task(self._memory_watchdog()))
        
        for task in tasks:
            pass
        
        # Wait indefinitely (tasks restart themselves)
        while True:
            await asyncio.sleep(1)

    async def _robust_main_loop(self):
        """Main loop with auto-restart on errors"""
        while True:
            try:
                await self._main_loop()
            except Exception as e:
                self.logger.error(f"Main loop crashed: {e}, restarting in 5 seconds...")
                if hasattr(self, 'buzzers'):
                    self.buzzers.control.play_error()
                await asyncio.sleep(5)
    
    async def _robust_web_server(self):
        """Web server with automatic restart on errors"""
        while True:
            try:
                await self._web_server.run() # type: ignore
            except Exception as e:
                self.logger.error(f"Web server crashed: {e}, restarting in 10 seconds...")
                await asyncio.sleep(10)

    async def _wifi_monitor(self):
        """WiFi connection monitoring with auto-reconnection"""
        while True:
            try:
                if not self.wifiManager.is_wifi_connected():
                    self.logger.warning("WiFi disconnected, attempting reconnect...")
                    await self.wifiManager.connect_wifi()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                self.logger.error(f"WiFi monitor error: {e}")
                await asyncio.sleep(60)
                            
    async def _main_loop(self):
        while True:
            await asyncio.sleep(0.5)
            # Periodically call the garbage collector
            if gc.mem_free() < 10000:  # If free memory is less than 10KB
                gc.collect()
        
    async def _memory_watchdog(self):
        """Memory monitoring with forced garbage collection"""
        while True:
            try:
                import gc
                free_mem = gc.mem_free()
                if free_mem < 8192: # Less than 8KB free memory
                    self.logger.warning(f"Low memory: {free_mem} bytes, forcing GC")
                    gc.collect()
                    
                    # If there is still not enough memory - reboot
                    if gc.mem_free() < 4096:
                        self.logger.critical("Critical memory shortage, rebooting...")
                        # Try to save states before reboot
                        try:
                            await self.cleanup()
                        except:
                            pass
                        import machine
                        machine.reset()
                        
                await asyncio.sleep(10)  # Check every 10 seconds
            except Exception as e:
                self.logger.error(f"Memory watchdog error: {e}")
                await asyncio.sleep(30)


# Create an instance of the Main class and run it
if __name__ == "__main__":
    main = None
    try:
        main = Main()
        asyncio.run(main.run())
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
        if main:
            asyncio.run(main.cleanup())
    except MemoryError:
        print("Memory error, attempting cleanup and rebooting...")
        if main:
            try:
                asyncio.run(main.cleanup())
            except:
                pass
        import machine
        machine.reset()
    except Exception as e:
        print(f"Fatal error: {e}")
        if main:
            try:
                asyncio.run(main.cleanup())
            except:
                pass
        import machine
        machine.reset()
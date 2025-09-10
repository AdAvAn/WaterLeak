from Sensors.LeakPort import LeakPort
import Resources.Settings as Settings
from State.States import States
import Helpers.DeviceNames as DeviceNames
from Buzzers.Buzzers import Buzzers
from Logging.AppLogger import AppLogger
import Helpers.DeviceStates as DeviceStates
from LCD.Display import Display
from Valves.WaterLineValves import WaterLineValves
from Heater.HeaterPowerSwith import HeaterPowerSwith
import uasyncio as asyncio

class LeakSensors:

    alarm_zones = None

    def __init__(self,  states:States, water_line_valves: WaterLineValves, heater: HeaterPowerSwith, display=None):
        self.states = states
        self.display = display
        self.water_line_valves = water_line_valves
        self._heater = heater
        self.logger = AppLogger()
        self.buzzers = Buzzers()
        self.zone_1_leak = LeakPort(DeviceNames.ZONE_1_LEAK_SENSORS_KEY, Settings.LEAK_ZONE1_PIN, self._zone_1_leak_handler)
        self.zone_2_leak = LeakPort(DeviceNames.ZONE_2_LEAK_SENSORS_KEY, Settings.LEAK_ZONE2_PIN, self._zone_2_leak_handler)
        self._zone_1_leak_triggered = self.zone_1_leak.is_detected_leak()
        self._zone_2_leak_triggered = self.zone_2_leak.is_detected_leak()
        self._alarm_acknowledged = False  # Flag to track if user acknowledged the alarm
        self._update_leaks_sensor_state()

    def is_detected_leaks(self) -> bool:
        return self._zone_1_leak_triggered == True or self._zone_2_leak_triggered == True
    
    def start(self):
        self.zone_1_leak.start()
        self.zone_2_leak.start()
        
        # Check for leaks detected during initialization and handle them
        if self.is_detected_leaks():
            self.logger.warning("LEAK SENSORS: Leaks detected during system startup - initiating emergency sequence")
            asyncio.create_task(self._handle_startup_leak_detection())
    
        self.logger.info(f"LEAK SENSORS: Leak sensor [{self.zone_1_leak.name} and {self.zone_2_leak.name}] has start monitoring")
        
    def stop(self):
        self.zone_1_leak.stop()
        self.zone_2_leak.stop()
        self.logger.info("LEAK SENSORS: Leak sensor monitoring has stoped")

    def clear(self):
         # Stop alarm sound
        self.buzzers.alarm.off()

        """Clear alarm sound and display, but keep sensor states until sensors are physically dry"""
        if self.is_detected_leaks(): 
            self._alarm_acknowledged = True
            # Return display to normal state
            if self.display: 
                self.display.reset_alarm()
        
        # Continue monitoring sensors to detect when they become dry
        # Don't restart sensors - they should continue running
        self.logger.info("LEAK SENSORS: Continuing to monitor sensors for dry state")

    # MARK: HELPERS
    def _update_leaks_sensor_state(self):
        zone1 = self.zone_1_leak.get_leak_state()
        zone2 = self.zone_2_leak.get_leak_state()
       
        # Update states in memory
        self.states.update_leak_sensor_state(self.zone_1_leak.name, zone1)
        self.states.update_leak_sensor_state(self.zone_2_leak.name, zone2)
        
        # Check if sensors became dry after leak was detected
        self._check_sensor_recovery()
        
        self.logger.debug(f"LEAK SENSOR: Update leak sensor state: ZONE 1: {zone1}, ZONE 2: {zone2}")

    def _check_sensor_recovery(self):
        """Check if sensors recovered (became dry) and reset triggers accordingly"""
        zone1_is_dry = not self.zone_1_leak.is_detected_leak()
        zone2_is_dry = not self.zone_2_leak.is_detected_leak()
        
        # Reset zone 1 trigger if sensor became dry
        if self._zone_1_leak_triggered and zone1_is_dry:
            self._zone_1_leak_triggered = False
            self.logger.info("LEAK SENSORS: Zone 1 sensor recovered (became dry)")
        
        # Reset zone 2 trigger if sensor became dry
        if self._zone_2_leak_triggered and zone2_is_dry:
            self._zone_2_leak_triggered = False
            self.logger.info("LEAK SENSORS: Zone 2 sensor recovered (became dry)")
        
        # If all sensors recovered, reset alarm acknowledgment and zones
        if not self.is_detected_leaks():
            self.logger.info("LEAK SENSORS: All sensors recovered - fully resetting alarm state")
            self._alarm_acknowledged = False
            self.alarm_zones = None
            if self.display: 
                self.display.reset_alarm()

    async def _handle_startup_leak_detection(self):
        """Handle leaks detected during system startup with the same algorithm as runtime detection"""
        try:
            # Give system a moment to stabilize after startup
            await asyncio.sleep(2)
            
            # Verify leaks are still detected after stabilization
            if self.is_detected_leaks():
                zones = self._get_alarm_zones()
                self.logger.critical(f"LEAK SENSORS: STARTUP LEAK DETECTION - Emergency sequence initiated for {zones}")
                
                # Step 1: Close valves immediately (same as runtime detection)
                self.water_line_valves.leak_detected()
                self.logger.warning("LEAK SENSORS: Emergency valve closure initiated during startup")
                
                # Step 2: Power off heater (same as runtime detection)
                self._heater.power_off()
                self.logger.warning("LEAK SENSORS: Heater powered off during startup")
                
                # Step 3: Start alarm buzzer
                self.buzzers.alarm.play_alarm()
                self.logger.warning("LEAK SENSORS: Alarm buzzer started during startup")
                await asyncio.sleep(0.1)  # Give alarm time to start
                
                # Step 4: Set zones and show alarm on display
                self.alarm_zones = zones
                if self.display:
                    self.logger.warning(f"LEAK SENSORS: Showing startup leak alarm on display: {zones}")
                    self.display.show_alarm("LEAK DETECTED", zones)
            else:
                self.logger.info("LEAK SENSORS: Startup leak check passed - sensors became dry during stabilization")
                
        except Exception as e:
            self.logger.error(f"LEAK SENSORS: Error in startup leak detection handler: {e}")

    def _zone_1_leak_handler(self, state:str) -> None:
        current_leak_detected = (state == DeviceStates.LEAK)
        
        # Update state in memory always
        self.states.update_leak_sensor_state(self.zone_1_leak.name, state)
        
        # If leak is detected and wasn't triggered before
        if current_leak_detected and not self._zone_1_leak_triggered:
            self._zone_1_leak_triggered = True
            self._alarm_acknowledged = False  # Reset acknowledgment on new leak
            self.logger.warning(f"LEAK SENSOR: NEW leak detected in ZONE 1")
            # Create async task to handle alarm sequence
            asyncio.create_task(self._handle_leak_alarm_async())
        
        # If no leak detected and was triggered before, sensor recovered
        elif not current_leak_detected and self._zone_1_leak_triggered:
            self._zone_1_leak_triggered = False
            self.logger.info(f"LEAK SENSOR: ZONE 1 sensor recovered (became dry)")
            
    def _zone_2_leak_handler(self, state:str) -> None:
        current_leak_detected = (state == DeviceStates.LEAK)
        
        # Update state in memory always
        self.states.update_leak_sensor_state(self.zone_2_leak.name, state)
        
        # If leak is detected and wasn't triggered before
        if current_leak_detected and not self._zone_2_leak_triggered:
            self._zone_2_leak_triggered = True
            self._alarm_acknowledged = False  # Reset acknowledgment on new leak
            self.logger.warning(f"LEAK SENSOR: NEW leak detected in ZONE 2")
            # Create async task to handle alarm sequence
            asyncio.create_task(self._handle_leak_alarm_async())
        
        # If no leak detected and was triggered before, sensor recovered
        elif not current_leak_detected and self._zone_2_leak_triggered:
            self._zone_2_leak_triggered = False
            self.logger.info(f"LEAK SENSOR: ZONE 2 sensor recovered (became dry)")

    async def _handle_leak_alarm_async(self):
        """Handle leak alarm sequence asynchronously to ensure proper timing"""
        try:
            zones = self._get_alarm_zones()
            
            # Only trigger full alarm sequence if alarm wasn't acknowledged yet
            if zones != self.alarm_zones and not self._alarm_acknowledged:
                if self.alarm_zones is None:
                    # Step 1: Close valves immediately
                    self.water_line_valves.leak_detected()
                    # Step 2: Power off heater
                    self._heater.power_off()
                    
                    # Step 3: Start alarm buzzer and give it time to initialize
                    self.logger.warning("LEAK SENSOR: Starting emergency sequence - closing valves and starting alarm")
                    self.buzzers.alarm.play_alarm()
                    await asyncio.sleep(0.1)  # Give alarm time to start
                    
                self.alarm_zones = zones
                
                # Step 4: Show alarm on display (only if not acknowledged)
                if self.display:  
                    self.logger.warning(f"LEAK SENSOR: Showing alarm on display: {zones}")
                    self.display.show_alarm("LEAK DETECTED", zones)
                    
        except Exception as e:
            self.logger.error(f"LEAK SENSOR: Error in alarm handler: {e}")

    def _get_alarm_zones(self):
        """Get current alarm zones based on triggered sensors"""
        if self._zone_1_leak_triggered and self._zone_2_leak_triggered:
            return "Zone 1 & Zone 2"
        elif self._zone_1_leak_triggered:
            return "Zone 1"
        elif self._zone_2_leak_triggered:
            return "Zone 2"
        else:
            return None
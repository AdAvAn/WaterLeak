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

class Main:
    def __init__(self):
        #Create utilits
        
        # Create Realtime modle 
        self.ds_rtc = DsRTC() 
        
        # Create State module 
        self.states = States()
        
        # Create Loger module 
        self.logger = AppLogger()
        
        # Create Buzzers module 
        self.buzzers = Buzzers()

        # Create Buzzers module 
        self.display = Display(self.states)
       
        # Create Valve
        self.water_line_valves = WaterLineValves(self.states, self.display)

        # Temp sensors
        self.temp_sensors = TempSensors(self.states)

        # Leak sensors
        self.leak_sensors = LeakSensors(self.states, self.display, self.water_line_valves)

        # Create Buttons
        self.valve_buttons = ColdHotValveButtons(self.water_line_valves, self.leak_sensors, self.display)

        # Heater Swith 
        self.heater_swith = HeaterPowerSwith(self.states)

        # Heater button
        self.heater_button = HeaterButton(self.states)
        
    async def startOperating(self):
        await self.ds_rtc.update_time()
        await asyncio.sleep(2)
        self.temp_sensors.start()
        self.leak_sensors.start()
        await asyncio.sleep(2)
        self.valve_buttons.start()
        self.heater_button.start()
        self.display.show_default_screens()
        self.display.start()

        if not self.leak_sensors.is_detected_leaks():
            self.buzzers.control.play_started_app()

    async def run(self): 
        await self.startOperating()
        self.logger.warning(f"Leak controller Started. Date: {self.ds_rtc.get_datetime_ddmmyy()}")
        while True:
            await asyncio.sleep(0.5)
          
    def cleanup(self):
        self.temp_sensors.stop()
        self.buzzers.control.off()
        self.leak_sensors.stop()
        self.valve_buttons.stop()
        self.water_line_valves.fircse_stop()
        self.display.lcd.set_brightness(15)
        self.logger.warning(f"Leak controller stoped. Date: {self.ds_rtc.get_datetime_ddmmyy()}")
        

# Create an instance of the Main class and run it
if __name__ == "__main__":
    main = Main()
    try:
        asyncio.run(main.run())  # Запуск асинхронного цикла
    except KeyboardInterrupt:
       main.cleanup()
        
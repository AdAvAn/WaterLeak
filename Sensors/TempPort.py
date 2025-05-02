
import machine
import onewire
import ds18x20
import uasyncio as asyncio

class TempPort:

    def __init__(self, name:str, pin_id:int):

        self.name = name
        self.pin = machine.Pin(pin_id)
        self.ds_sensor = ds18x20.DS18X20(onewire.OneWire(self.pin))
        self.rom = None

        roms = self.ds_sensor.scan()
        if roms:
            self.rom = roms[0] 
        else:
            raise Exception(f"TEMP-PORT: Temp sensor not found on pin {self.name}")
        

    async def read_temperature(self) -> float:
        if self.rom:
            self.ds_sensor.convert_temp()
            await asyncio.sleep(0.9)
            return self.ds_sensor.read_temp(self.rom)
        else:
            raise Exception(f"TEMP-PORT: Temp sensor {self.name} not found")
        
    def get_name(self) ->str:
        return self.name
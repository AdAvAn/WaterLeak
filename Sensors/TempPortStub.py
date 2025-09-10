import uasyncio as asyncio
from Logging.AppLogger import AppLogger

class TempPortStub:
    """Stub for temperature sensor when sensor is not connected"""
    
    def __init__(self, name: str, pin_id: int, reason: str = "Sensor not found"):
        self.name = name
        self.pin_id = pin_id
        self.reason = reason

    async def read_temperature(self) -> str:
        """Always returns special value indicating sensor absence"""
        return "No temp sensor"
        
    def get_name(self) -> str:
        return self.name
    
    def get_reason(self) -> str:
        """Returns the reason why stub is being used"""
        return self.reason
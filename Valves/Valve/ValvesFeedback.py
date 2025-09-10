# from machine import Pin

# class ValvesFeedback:
    
#     def __init__(self, pin_number, error_handler):
#         self.pin = Pin(pin_number, Pin.IN, Pin.PULL_UP)
#         self.error_handler = error_handler
#         self.pin.irq(trigger=Pin.IRQ_FALLING, handler=self._pin_callback)
    
#     def _pin_callback(self, pin) -> None:
#         if self.is_detected_error():
#             self.error_handler()

#     def is_detected_error(self) -> bool:
#         return self.pin.value() == 0


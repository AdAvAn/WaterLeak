# system packages
from machine import I2C
import gc
from time import sleep, sleep_ms, sleep_us

# custom packages
from . import const as Const

class WSLCD1602RGB:
  
    def __init__(self, _I2C:I2C, custom_symbols:dict, default_brightness:int, _default_color = (144, 249, 15)):
        self._I2C = _I2C
        self._row = 16
        self._col = 2
        self._default_color = _default_color
        self.available_custom_symbols = custom_symbols
        self.custom_symbols_loaded = {}
        self._current_brightness_persent = default_brightness
        self._showfunction = Const.LCD_4BITMODE | Const.LCD_8BITMODE | Const.LCD_2LINE | Const.LCD_5x8DOTS
        self.begin()
        gc.collect()

    # MARK: HELPERS
    def _write_command(self, cmd):
        self._I2C.writeto_mem(Const.LCD_ADDRESS, Const.LCD_SETDDRAMADDR, chr(cmd))
        # sleep_us(43)

    def _write_data(self, data):
        self._I2C.writeto_mem(Const.LCD_ADDRESS, Const.LCD_SETCGRAMADDR, chr(data))
        # sleep_us(43)

    def _set_rgb_reg(self, reg, data):
        self._I2C.writeto_mem(Const.RGB_ADDRESS, reg, chr(data))

    # MARK: DISPLAY
    def show_cursor(self):
        self._write_command(Const.LCD_DISPLAYCONTROL |  Const.LCD_DISPLAYON | Const.LCD_CURSORON)

    def hide_cursor(self):
        self._write_command(Const.LCD_DISPLAYCONTROL | Const.LCD_DISPLAYON | Const.LCD_CURSOROFF)

    def blink_cursor_on(self):
        self._write_command(Const.LCD_DISPLAYCONTROL | Const.LCD_DISPLAYON | Const.LCD_CURSORON | Const.LCD_BLINKON)

    def display_on(self):
        """
        Turn the display on

        Show the characters on the LCD display, this is the normal behaviour.
        This method should only be used after no_display() has been used.

        @see no_display
        """
        self._write_command(Const.LCD_DISPLAYCONTROL | Const.LCD_DISPLAYON)

    def display_off(self):
        """
        Turn the display off

        Do not show any characters on the LCD display. Backlight state will
        remain unchanged. Also all characters written on the display will
        return, when the display in enabled again.

        @see display
        """
        self._write_command(Const.LCD_DISPLAYCONTROL | Const.LCD_DISPLAYOFF)

    def off_backlight(self):
        self.set_colour_black()

    # MARK: COLORS

    def get_brightness(self) -> int:
        return self._current_brightness_persent
    
    def reset_brightness_to_default(self):
        self.set_brightness(100)

    def set_brightness(self, brightness_percent):
        if not (0 <= brightness_percent <= 100):
            brightness_percent = 100
        self._current_brightness_persent = brightness_percent
        brightness = int((brightness_percent / 100) * 255)
        self._set_rgb_reg(Const.GRPPWM, brightness)

    def set_rgb(self, red, green, blue):
        if not (0 <= red <= 255) or not (0 <= green <= 255) or not (0 <= blue <= 255):
            raise ValueError(f"The color value must be between 0 and 255. Red:{red}, Green:{green}, Blue:{blue} ")
        
        self._set_rgb_reg(Const.REG_RED, red)
        self._set_rgb_reg(Const.REG_GREEN, green)
        self._set_rgb_reg(Const.REG_BLUE, blue)

    def set_colour_white(self):
        self.set_rgb(255, 255, 255)

    def set_colour_black(self):
        self.set_rgb(0, 0, 0)

    def set_color(self, color):
        if not color:
            self.set_rgb(*self._default_color)
        elif isinstance(color, tuple) and len(color) == 3:
            self.set_rgb(*color)

    # MARK: TEXT
    def set_cursor(self,col,row):
        if(row == 0):
            col|=0x80
        else:
            col|=0xc0
        self._I2C.writeto(Const.LCD_ADDRESS, bytearray([Const.LCD_SETDDRAMADDR,col]))
        # sleep_us(43)

    # Modified method to clear display and custom symbols
    def clear(self):
        self._write_command(Const.LCD_CLEARDISPLAY)
        # sleep_ms(153)
        
    def print_out(self, string: str):
        i = 0
        while i < len(string):
            matched = False
            # Check any key in the word available_custom_symbols
            for key in self.available_custom_symbols.keys():
                key_length = len(key)
                # Check that you don't have to look at the edge of the previous string
                if i + key_length <= len(string) and string[i:i+key_length] == key:
                    symbols_index = self.custom_symbols_loaded.get(key)
                    if symbols_index is not None:
                        self._write_data(symbols_index)
                        i += key_length
                        matched = True
                        break
            
           # If you don't need a special symbol
            if not matched:
               # Check Index to get IndexError
                if i < len(string):
                    self._write_data(ord(string[i]))
                    i += 1


    def load_custom_symbol(self, key:str, symbol_data:list):
        symbol_index = len(self.custom_symbols_loaded)
        if symbol_index > 7:
            raise ValueError("No more space for custom symbols")
        self._write_command(Const.LCD_SETCGRAMADDR | (symbol_index << 3))
        for line in symbol_data:
            self._write_data(line)
        self.custom_symbols_loaded[key] = symbol_index

    def load_custom_symbols(self, symbols: list):
        for key in symbols:
            if key in self.available_custom_symbols:
                symbol_data = self.available_custom_symbols[key]
                self.load_custom_symbol(key, symbol_data)

    # Method to clear custom symbols from CGRAM
    def clear_custom_symbols(self):
        self.custom_symbols_loaded = {}

    def display(self):
        self._showcontrol |= Const.LCD_DISPLAYON 
        self._write_command(Const.LCD_DISPLAYCONTROL | self._showcontrol)
 
    def begin(self):
        if (self._row > 1):
            self._showfunction |= Const.LCD_2LINE 

        self._currline = 0 
        sleep(0.05)
        # Send function set command sequence
        self._write_command(Const.LCD_FUNCTIONSET | self._showfunction)
        #delayMicroseconds(4500);  # wait more than 4.1ms
        sleep(0.005)
        # second try
        self._write_command(Const.LCD_FUNCTIONSET | self._showfunction)
        #delayMicroseconds(150);
        sleep(0.005)
        # third go
        self._write_command(Const.LCD_FUNCTIONSET | self._showfunction)
        # finally, set # lines, font size, etc.
        self._write_command(Const.LCD_FUNCTIONSET | self._showfunction)
        # turn the display on with no cursor or blinking default
        self._showcontrol = Const.LCD_DISPLAYON | Const.LCD_CURSOROFF | Const.LCD_BLINKOFF 
        self.display()
        # clear it off
        self.clear()
        # Initialize to default text direction (for romance languages)
        self._showmode = Const.LCD_ENTRYLEFT | Const.LCD_ENTRYSHIFTDECREMENT 
        # set the entry mode
        self._write_command(Const.LCD_ENTRYMODESET | self._showmode)
        # backlight init
        self._set_rgb_reg(Const.REG_MODE1, 0)
        # set LEDs controllable by both PWM and GRPPWM registers
        self._set_rgb_reg(Const.REG_OUTPUT, 0xFF)
        # set MODE2 values
        # 0010 0000 -> 0x20  (DMBLNK to 1, ie blinky mode)
        self._set_rgb_reg(Const.REG_MODE2, 0x00)
        self.set_brightness(self._current_brightness_persent)
       



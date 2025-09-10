from ..Driver.WSLCD1602RGB import  WSLCD1602RGB
import Helpers.DisplayColors as Colors
import Helpers.Helpers as Helpers
import Helpers.LcdCustomSymbols as Symbols
import gc

class Screen:
    
    _default_text = "--"

    def __init__(self, lcd: WSLCD1602RGB, screen_name:str, device_name:str, screen_title:str, color:tuple):
        self.lcd = lcd
        self.screen_name = screen_name 
        self.device_name = device_name
        self.screen_title = screen_title
        self._default_screan_color = color if (color is not None and Helpers.is_correct_color(color)) else Colors.BLUE_AND_WHITE

    # Prsenter
    def present(self):
         raise NotImplementedError("Subclass must implement abstract method set_state")
    
    def show(self, message, color = None):
        self._config_lcd(message, color)
        self._show_title()
        self._show_description(message)
        gc.collect()

    def update_description(self, message):
        self._show_description(message)

    # Setter
    def set_screen_title(self, title) -> None:
        self.screen_title = title

    def set_device_name(self, device_name: str):
        self.device_name = device_name

    # Getters
    def get_device_name(self) -> str:
        return self.device_name
    
    def get_screen_name(self) -> str:
        return self.screen_name
    
    def get_screen_title(self) -> str:
        return self.screen_title

    def get_default_color(self):
        return self._default_screan_color
    
    def get_default_text(self):
        return self._default_text

    # Helpers
    def _config_lcd(self, message: str, color = None):
        self._load_screan_symbols(message)
        self.lcd.clear()
        color = color if color else self._default_screan_color
        self.lcd.set_color(color)

    def _show_title(self):
        self.lcd.set_cursor(col=0, row=0)
        title = self.screen_title if self.screen_title is not None else self._default_text
        self.lcd.print_out(title)

    def _show_description(self, text = None):
        self.lcd.set_cursor(col=0, row=1)
        message = text if text is not None else self._default_text
        self.lcd.print_out(message)

    # Finds special characters by the pattern -intintint- in the text and adds them as an array for downloading
    def _find_screen_symbols(self, title: str, message: str) -> list:
        combined_str = title + message
        pos = 0
        out = []
        n = len(combined_str)
        while pos < n:
            start = combined_str.find('-', pos)
            if start == -1:
                break
            if start + 5 <= n and combined_str[start + 1:start + 4].isdigit() and combined_str[start + 4] == '-':
                symbol = combined_str[start:start + 5]
                out.append(symbol)
                pos = start + 5
            else:
                pos = start + 1
        return out

    def _load_screan_symbols(self, message:str) -> None:
        screan_symbols = self._find_screen_symbols(self.screen_title, message)
        if screan_symbols:
            self.lcd.clear_custom_symbols()
            self.lcd.load_custom_symbols(screan_symbols)


    def __eq__(self, other):
        return self.screen_name == other.screen_name and self.device_name == other.device_name


    def __hash__(self):
        return hash(self.screen_name + self.device_name)
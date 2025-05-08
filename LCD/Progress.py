from .Driver.WSLCD1602RGB import WSLCD1602RGB
from .Screens.ProgressScreen import ProgressScreen
import Helpers.DisplayNames as DisplayNames
import LCD.Display 

class Progress:

    def __init__(self, lcd: WSLCD1602RGB, display:LCD.Display.Display):
        self.lcd = lcd
        self._display = display

    def update_progress(self, title:str, device_name: str, progress_vlaue: float):
        progress_screan = self._display.get_screen_at_device_name(device_name)
       
        can_clear_display = self._display.gen_number_of_screens() > 1
        if progress_screan is not None:
            progress_screan.update_progress(progress_vlaue, can_clear_display) # type: ignore
        else:
            progress_screan = ProgressScreen(lcd=self.lcd, screen_title=title, device_name=device_name)
            progress_screan.update_progress(progress_vlaue, can_clear_display)
            self._display.add_new_progress_screens(progress_screan)

        if progress_vlaue >= 1.0:
             self._progress_completion(progress_screan)
    
                 
    def _progress_completion(self, progress_screan):
        from Buzzers.Buzzers import Buzzers
        self.buzzers = Buzzers()
        device_name:str = progress_screan.get_device_name()
        self._display.remove_screen(progress_screan)
        self.buzzers.control.play_done()
        if self._display.is_exist_screens() == False:
            self._display.show_carusel(device_name) # type: ignore

    
     
    
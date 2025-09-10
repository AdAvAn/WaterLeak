import Helpers.DisplayColors as Colors
import Helpers.DisplayNames as DisplayNames
import Helpers.DeviceNames as DeviceNames
from ..Driver.WSLCD1602RGB import  WSLCD1602RGB
from .Screen import Screen

class ProgressScreen(Screen):

    _progress_bar = ""
    _progress_bar_preview = None

    def __init__(self, lcd: WSLCD1602RGB, screen_title:str, device_name:str):
        super().__init__(
            lcd = lcd, 
            screen_name = DisplayNames.PROGRESS_SCREEN_NAME,
            device_name = device_name, 
            screen_title = screen_title,
            color = Colors.GHOST_WHITE
        )

    def present(self):
        self.show(self._progress_bar)
  
    def update_progress(self, progress_vlaue: float, can_clear: bool):
        self._progress_bar = self._create_progres_bar(progress_vlaue)
        self._can_clear = can_clear
         
    def _create_progres_bar(self, progress_vlaue: float) -> str:
        progress = min(max(int(progress_vlaue * 16), 0), 16)
        progress_bar = "-" * progress
        if progress < 16:
            progress_bar = progress_bar + ">"
        return progress_bar



class Error:
    def __init__(self, code: str, message: str, original = None):
        self._code = code
        self._message = message
        self.original = original

    def get_message(self) -> str:
        if self.original:
            return self._message + f" (Original exception: {str(self.original)})"
        else:
            return self._message

    def get_code(self) -> str:
        return self._code
    
    def set_original_errror(self, original) -> None:
        self.original = original
    
    def get_original(self):
        return self.original

    def show_error(self) -> None:
        print(f"ERROR: {self._code}")
        print(f"DESCRIPTION: {self._message}")
        if self.original:
            print(f"ORIGINAL EXCEPTION: {str(self.original)}")

class Errors:
    @staticmethod
    def UNKNOWN_ERROR() -> Error:
        return Error("ERR100", "Unknown error")

    @staticmethod
    def INCORRECT_SETTINGS_CONFIGURATION() -> Error:
        return Error("ERR101", "Incorrect settings configuration")

    @staticmethod
    def FAILED_READ_CONFIG_FILE() -> Error:
        return Error("ERR102", "Error reading config file")

    @staticmethod
    def FAILED_READ_STATES_FILE() -> Error:
        return Error("ERR103", "Error reading states from file")
    
    @staticmethod
    def FAILED_WRITE_STATES_FILE() -> Error:
        return Error("ERR104", "Error writing state to file")
    
    

class AppException(Exception):
    
    def __init__(self, error: Error, original = None):
        self._error = error
        self._error.set_original_errror(original)
        
        super().__init__(self._error.get_message())

    def get_error_code(self) -> str:
        return self._error.get_code()

    def get_error_message(self) -> str:
        return self._error.get_message()

    def get_original_exception(self):
        return self._error.get_original()
    
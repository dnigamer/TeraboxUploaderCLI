from datetime import datetime

from colorama import Fore, Back, Style


class Formatting:
    """
    This class is used to format the output of the program. It uses the colorama library to color the output.
    """
    def __init__(self, timestamps=False):
        """
        This method initializes the colorama library.
        :param timestamps: If True, the output will be formatted with a timestamp.
        """
        if timestamps:
            self.timestamps = True
        else:
            self.timestamps = False
        self.fore = Fore
        self.back = Back
        self.style = Style

    def timestamp(self) -> str:
        """
        This method is used to format a message with a timestamp.
        :return:
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if self.timestamps else ''
        return f"{self.style.BRIGHT}{self.fore.WHITE}[{timestamp}]{self.style.RESET_ALL}"

    def error(self, msg_type: str, message: str) -> None:
        """
        This method is used to format a error message.
        :param msg_type: Add a classification to the logged message.
        :param message: The error message.
        :return:
        """
        return print(f"{self.timestamp()}{self.fore.RED} {msg_type.upper()} ERROR: {self.style.RESET_ALL}{message}")

    def warning(self, msg_type: str, message: str) -> None:
        """
        This method is used to format a warning message.
        :param msg_type: Add a classification to the logged message.
        :param message: The warning message.
        :return:
        """
        return print(f"{self.timestamp()}{self.fore.YELLOW} {msg_type.upper()} WARNING: {self.style.RESET_ALL}{message}")

    def success(self, msg_type: str, message: str) -> None:
        """
        This method is used to format a success message.
        :param msg_type: Add a classification to the logged message.
        :param message: The success message.
        :return:
        """
        return print(f"{self.timestamp()}{self.fore.GREEN} {msg_type.upper()} SUCCESS: {self.style.RESET_ALL}{message}")

    def info(self, msg_type: str, message: str) -> None:
        """
        This method is used to format an info message.
        :param msg_type: Add a classification to the logged message.
        :param message: The info message.
        :return:
        """
        return print(f"{self.timestamp()}{self.fore.CYAN} {msg_type.upper()} INFO: {self.style.RESET_ALL}{message}")

    def debug(self, msg_type: str, message: str) -> None:
        """
        This method is used to format a debug message.
        :param msg_type: Add a classification to the logged message.
        :param message: The debug message.
        :return:
        """
        return print(f"{self.timestamp()}{self.fore.MAGENTA} {msg_type.upper()} DEBUG: {self.style.RESET_ALL}{message}")
import os
import shutil
import sys
from enum import Enum
from typing import Any, Optional

# Global variable to control color output
_use_colors = True
_loading_bars = ["—", "\\", "|", "/"]
_loading_bars_index = -1


class Color(Enum):
    """ANSI color codes"""

    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    @staticmethod
    def supports_color() -> bool:
        """Check if the terminal supports color output"""
        # If the NO_COLOR env var is set, then we shouldn't use color
        if os.environ.get("NO_COLOR", "") != "":
            return False

        # If the FORCE_COLOR env var is set, then we should use color
        if os.environ.get("FORCE_COLOR", "") != "":
            return True

        # isatty is not always implemented
        is_a_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

        # Windows has specific checks for color support
        if sys.platform == "win32":
            return is_a_tty and (
                "ANSICON" in os.environ or "WT_SESSION" in os.environ or os.environ.get("TERM_PROGRAM") == "vscode"
            )

        # For all other platforms, assume color support if it's a TTY
        return is_a_tty


def set_color_mode(enabled: bool) -> None:
    """Set whether to use colors in output"""
    global _use_colors
    _use_colors = enabled


def info(message: Any) -> None:
    """Print an information message in cyan color"""
    if _use_colors and Color.supports_color():
        print(f"{Color.CYAN.value}{message}{Color.RESET.value}")
    else:
        print(message)


def warning(message: Any) -> None:
    """Print a warning message in yellow color"""
    if _use_colors and Color.supports_color():
        print(f"{Color.YELLOW.value}{message}{Color.RESET.value}")
    else:
        print(message)


def error(message: Any) -> None:
    """Print an error message in red color"""
    if _use_colors and Color.supports_color():
        print(f"{Color.RED.value}{message}{Color.RESET.value}")
    else:
        print(message)


def success(message: Any) -> None:
    """Print a success message in green color"""
    if _use_colors and Color.supports_color():
        print(f"{Color.GREEN.value}{message}{Color.RESET.value}")
    else:
        print(message)


def progress(message: Any) -> None:
    """Print a progress/status update message in blue color"""
    if _use_colors and Color.supports_color():
        print(f"{Color.BLUE.value}{message}{Color.RESET.value}")
    else:
        print(message)


def highlight(message: Any) -> None:
    """Print an important message in magenta color"""
    if _use_colors and Color.supports_color():
        print(f"{Color.MAGENTA.value}{Color.BOLD.value}{message}{Color.RESET.value}")
    else:
        print(message)


def input_prompt(message: Any) -> str:
    """Display a colored input prompt and return user input"""
    if _use_colors and Color.supports_color():
        return input(f"{Color.WHITE.value}{Color.BOLD.value}{message}{Color.RESET.value}")
    else:
        return input(message)


# Store the last progress bar state for message updates
_last_progress = None
_has_started = False
_previous_messages = []
_last_chunk_size = 0


def progress_bar(
    current: int,
    total: int,
    bar_length: int = 30,
    prefix: str = "",
    suffix: str = "",
    message: str = "",
    message_color: Color = None,
    isPrompt: bool = False,
    isLoading: bool = False,
    isSending: bool = False,
    chunk_size: int = 0,
) -> None:
    """
    Display a colored progress bar with an optional message underneath

    Args:
        current: Current progress value
        total: Total value for 100% completion
        bar_length: Length of the progress bar in characters
        prefix: Text to display before the progress bar
        suffix: Text to display after the progress bar
        message: Optional message to display below the progress bar
        message_color: Color to use for the message
    """
    global _last_progress, _has_started, _previous_messages, _loading_bars_index, _last_chunk_size

    # Save the current state for message updates
    _last_progress = {
        "current": current,
        "total": total,
        "bar_length": bar_length,
        "prefix": prefix,
        "suffix": suffix,
    }

    _last_chunk_size = chunk_size

    # Get terminal width
    terminal_width = shutil.get_terminal_size().columns

    # Create the progress bar
    progress_ratio = (current + chunk_size) / total if total > 0 else 0
    filled_length = int(bar_length * progress_ratio)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)
    percentage = int(100 * progress_ratio)
    progress_text = f"{prefix} |{bar}| {percentage}% ({current + chunk_size}/{total})"
    # Format the progress bar line
    if suffix:
        progress_text = f"{progress_text} {suffix}"
    if isLoading:
        progress_text = f"{progress_text} | Processing {_loading_bars[_loading_bars_index]}"
    elif current < total and isSending:
        progress_text = f"{progress_text} | Sending batch ↑↑↑"

    # Handle the clearing of lines based on whether we've shown a message

    if _has_started:
        sys.stdout.write(" " * terminal_width)
        for i in range(len(_previous_messages)):
            sys.stdout.write("\033[F" + " " * terminal_width + "\r")
        sys.stdout.write("\033[F" + " " * terminal_width)
        sys.stdout.write("\033[F" + " " * terminal_width + "\r")
    else:
        _has_started = True

    # Apply colors if enabled
    if _use_colors and Color.supports_color():
        progress_text = progress_text.replace("█", f"{Color.GREEN.value}█{Color.BLUE.value}")
        progress_text = progress_text.replace("↑", f"{Color.GREEN.value}↑{Color.BLUE.value}")
        for i in range(len(_loading_bars)):
            progress_text = progress_text.replace(
                _loading_bars[i], f"{Color.GREEN.value}{_loading_bars[i]}{Color.BLUE.value}"
            )
        progress_text = f"{Color.BLUE.value}{progress_text}{Color.RESET.value}"

    sys.stdout.write(progress_text)
    sys.stdout.write("\n\n")

    if len(_previous_messages) > 0 and "waiting" in _previous_messages[-1]["message"].lower():
        _previous_messages.pop()

    for i in range(len(_previous_messages)):
        if _use_colors and Color.supports_color():
            color_code = _previous_messages[i]["color"].value if _previous_messages[i]["color"] else Color.YELLOW.value
            sys.stdout.write(f"{color_code}{_previous_messages[i]['message']}{Color.RESET.value}\n")
        else:
            sys.stdout.write(_previous_messages[i]["message"] + "\n")
    if message:
        if _use_colors and Color.supports_color():
            color_code = message_color.value if message_color else Color.YELLOW.value
            if isPrompt:
                sys.stdout.write(f"{color_code}{Color.BOLD.value}{message}{Color.RESET.value}")
                user_prompt = input()
                sys.stdout.write("\033[F" + " " * terminal_width + "\r")
            else:
                _previous_messages.append({"message": message, "color": message_color})
                sys.stdout.write(f"{color_code}{message}{Color.RESET.value}" + "\n")
        else:
            if isPrompt:
                sys.stdout.write(message)
                user_prompt = input()
                sys.stdout.write("\033[F" + " " * terminal_width + "\r")
            else:
                _previous_messages.append({"message": message, "color": message_color})
                sys.stdout.write(message + "\n")
    sys.stdout.flush()
    return user_prompt if isPrompt else None


def info_with_progress(message: Any, chunk_size: int = 0, isSending: bool = False) -> None:
    """Update the progress bar with an info message"""
    progress_bar(
        **_last_progress, message=message, message_color=Color.CYAN, chunk_size=chunk_size, isSending=isSending
    )


def warning_with_progress(message: Any, chunk_size: int = 0, isSending: bool = False) -> None:
    """Update the progress bar with a warning message"""
    progress_bar(
        **_last_progress, message=message, message_color=Color.YELLOW, chunk_size=chunk_size, isSending=isSending
    )


def error_with_progress(message: Any, chunk_size: int = 0, isSending: bool = False) -> None:
    """Update the progress bar with an error message"""
    progress_bar(**_last_progress, message=message, message_color=Color.RED, chunk_size=chunk_size, isSending=isSending)


def success_with_progress(message: Any, chunk_size: int = 0, isSending: bool = False) -> None:
    """Update the progress bar with a success message"""
    progress_bar(
        **_last_progress, message=message, message_color=Color.GREEN, chunk_size=chunk_size, isSending=isSending
    )


def highlight_with_progress(message: Any, chunk_size: int = 0, isSending: bool = False) -> None:
    """Update the progress bar with a highlighted message"""
    progress_bar(
        **_last_progress, message=message, message_color=Color.MAGENTA, chunk_size=chunk_size, isSending=isSending
    )


def input_prompt_with_progress(message: Any) -> str:
    """Update the progress bar with an input prompt message"""
    return progress_bar(**_last_progress, message=message, message_color=Color.WHITE, isPrompt=True)


def update_loading_animation(chunk_size: int = 0) -> None:
    """Update the loading animation in the progress bar"""
    global _loading_bars_index
    _loading_bars_index = (_loading_bars_index + 1) % len(_loading_bars)
    progress_bar(**_last_progress, message="", message_color=None, isLoading=True, chunk_size=chunk_size)


def get_last_chunk_size() -> int:
    """Get the last chunk size used in the progress bar"""
    return _last_chunk_size

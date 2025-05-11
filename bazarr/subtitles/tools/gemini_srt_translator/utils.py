import importlib.metadata
import subprocess
import sys
import threading
import time

import requests

from .logger import (
    error,
    highlight,
    info,
    input_prompt,
    progress,
    progress_bar,
    set_color_mode,
    success,
    warning,
)


def get_installed_version(package_name):
    """Returns the installed version of a package, or None if not installed."""
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def get_latest_pypi_version(package_name):
    """Fetches the latest version of a package from PyPI."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data["info"]["version"]
    return None


def display_progress_bar(stop_event, package_name):
    """Display a custom progress bar."""
    width = 40
    position = 0
    direction = 1  # 1 for right, -1 for left
    bar_length = 10  # Length of the moving part

    while not stop_event.is_set():
        # Update position
        position += direction

        # Change direction if hitting the boundaries
        if position >= width - bar_length or position <= 0:
            direction *= -1

        # Create the progress bar
        bar = "[" + " " * position + "#" * bar_length + " " * (width - position - bar_length) + "]"
        sys.stdout.write(f"\rInstalling {package_name}: {bar}")
        sys.stdout.flush()
        time.sleep(0.1)

    # Show complete when done
    bar = "[" + "#" * width + "]"
    sys.stdout.write(f"\rInstalling {package_name}: {bar} Complete!")
    sys.stdout.flush()


def upgrade_package(package_name, use_colors=True):
    """Upgrades the package using pip if an update is available."""
    installed_version = get_installed_version(package_name)
    latest_version = get_latest_pypi_version(package_name)

    set_color_mode(use_colors)

    if installed_version < latest_version:
        info(f"There is a new version of {package_name} available: {latest_version}.")
        answer = input_prompt(
            f"Do you want to upgrade {package_name} from version {installed_version} to {latest_version}? (y/n): "
        )
        if answer.lower() == "y":
            highlight(f"Upgrading {package_name}...")

            # Create and start a progress bar in a separate thread
            stop_progress = threading.Event()
            progress_thread = threading.Thread(target=display_progress_bar, args=(stop_progress, package_name))
            progress_thread.start()

            try:
                # Run pip install with stderr redirected to suppress pip update notifications
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "--upgrade",
                        package_name,
                        "--quiet",
                        "--disable-pip-version-check",
                    ],
                    check=True,
                    stderr=subprocess.DEVNULL,
                )
            finally:
                # Stop the progress bar
                stop_progress.set()
                progress_thread.join()

            success(f"\n{package_name} upgraded to version {latest_version}.")
            info("Please restart your script.\n")
            exit(0)
        else:
            info(f"{package_name} upgrade skipped.\n")

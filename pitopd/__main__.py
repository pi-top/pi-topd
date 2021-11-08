import logging
from signal import SIGINT, SIGTERM, signal

import click
import click_logging
from systemd.daemon import notify

from .app import App

logger = logging.getLogger()
click_logging.basic_config(logger)


@click.command()
@click_logging.simple_verbosity_option(logger)
@click.version_option()
def main() -> None:
    app = App()

    for sig in [SIGINT, SIGTERM]:
        signal(sig, lambda x, _: app.stop())

    # Blocking
    successful_start = app.start()

    # After main loop
    notify("STOPPING=1")

    if not successful_start:
        logger.error("Unable to start pi-topd")
        app.stop()

    # Exiting with 1 will cause systemd service to restart - we should only do this if we failed to determine a device ID
    exit(0 if app.device_id is not None else 1)

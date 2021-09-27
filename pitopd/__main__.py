from os import environ
from signal import SIGINT, SIGTERM, signal

import click
from pitop.common.logger import PTLogger
from systemd.daemon import notify

from .app import App


@click.command()
@click.option(
    "--log-level",
    type=int,
    help="set logging level from 10 (more verbose) to 50 (less verbose)",
    default=20,
    show_default=True,
)
@click.version_option()
def main(log_level) -> None:
    # Set the display env var
    environ["DISPLAY"] = ":0.0"

    PTLogger.setup_logging(
        logger_name="pi-topd", logging_level=log_level, log_to_journal=False
    )

    app = App()

    for sig in [SIGINT, SIGTERM]:
        signal(sig, lambda x, _: app.stop())

    # Blocking
    successful_start = app.start()

    # After main loop
    notify("STOPPING=1")

    if not successful_start:
        PTLogger.error("Unable to start pi-topd")
        app.stop()

    # Exiting with 1 will cause systemd service to restart - we should only do this if we failed to determine a device ID
    exit(0 if app.device_id is not None else 1)

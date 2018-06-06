#!/usr/bin/python

import sys
import click
import signal
import logging
import pyBus_core as core


def signal_handler_quit(signal, frame):
  """Manage Ctrl+C gracefully"""
  logging.info("Shutting down pyBus")
  core.shutdown()
  sys.exit(0)


def configure_logging(numeric_level):
  """Configure Logging"""
  if not isinstance(numeric_level, int):
    numeric_level=0
  logging.basicConfig(
    level=numeric_level,
    format='%(asctime)s [%(levelname)s in %(module)s] %(message)s', 
    datefmt='%Y/%m/%dT%I:%M:%S'
  )


#####################################
# MAIN
#####################################
@click.command()
@click.option('-v', '--verbose', count=True)
@click.option('-d', '--device', default="/dev/ttyUSB0")
def start_pybus(verbose, device):
  signal.signal(signal.SIGINT, signal_handler_quit)  # Manage Ctrl+C
  configure_logging(verbose)
  try:
    core.initialize(device)
    core.run()
  except Exception:
    logging.exception("Caught unexpected exception:")


if __name__ == "__main__":
  start_pybus()

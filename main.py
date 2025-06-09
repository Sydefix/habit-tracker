"""
Main entry point for the Habit Tracker application.

This script serves as a conventional entry point that simply calls the
command-line interface defined in cli.py.

To see all available commands, run:
    python main.py --help
"""

from cli import cli

if __name__ == "__main__":
    # This calls the click command group defined in cli.py
    cli()
"""
Main Command-Line Interface for the Habit Tracker application.

This module uses the 'click' library to create a powerful and user-friendly
CLI. It defines the main command group and all subcommands for managing,
analyzing, and interacting with both production and demo habit databases.
"""
"""
Main Command-Line Interface for the Habit Tracker application.

This module uses the 'click' library to create a powerful and user-friendly
CLI. It defines the main command group and all subcommands for managing,
analyzing, and interacting with both production and demo habit databases.
"""

import os

import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound

from . import analysis
from .fixtures import get_fixtures
from .habit_manager import PERIODICITIES, HabitManager
from .models import Base, Completion, Habit

# --- Database Setup ---
# Production Database
PROD_DB_URL = "sqlite:///./production_habits.db"
PROD_ENGINE = create_engine(PROD_DB_URL, echo=False)
ProdSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=PROD_ENGINE)

# Demo Database
DEMO_DB_URL = "sqlite:///./demo_habits.db"
DEMO_ENGINE = create_engine(DEMO_DB_URL, echo=False)
DemoSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=DEMO_ENGINE)

# Ensure production tables are created on script load
Base.metadata.create_all(bind=PROD_ENGINE)


# --- Click Command Groups ---


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.pass_context
def cli(ctx: click.Context):
    """A Command-Line Interface for managing and analyzing habits.

    By default, commands run on the production database.
    Use the 'demo' command for a sandboxed environment.

    Args:
        ctx (click.Context): The context object passed by Click, used to
            share state with subcommands.
    """
    # Store the production session factory in the context by default.
    # Subcommands like 'demo' can override this.
    ctx.obj = {"session_factory": ProdSessionLocal}


@cli.group()
@click.pass_context
def demo(ctx: click.Context):
    """A playground to test habits using a separate demo database.

    First, run 'demo start' to create the environment.
    Then, run any command like 'demo list' or 'demo analyze'.

    Args:
        ctx (click.Context): The context object. This command's primary
            purpose is to switch the session factory in the context to
            point to the demo database for all its subcommands.
    """
    demo_db_file = "demo_habits.db"

    if (
        not os.path.exists(demo_db_file)
        and ctx.invoked_subcommand not in ["start", "reset"]
    ):
        click.secho("Error: Demo database not found.", fg="red")
        click.echo("Please run 'habit demo start' to create it.")
        ctx.exit()

    ctx.obj["session_factory"] = DemoSessionLocal


@demo.command(name="start")
def start_demo():
    """Creates and seeds the demo database if it doesn't exist."""
    demo_db_file = "demo_habits.db"
    if os.path.exists(demo_db_file):
        click.echo("Demo database already exists.")
        click.echo(
            "You can continue using it, or run 'habit demo reset' to start over."
        )
        return

    click.echo("Creating new demo database...")
    Base.metadata.create_all(bind=DEMO_ENGINE)
    db = DemoSessionLocal()
    try:
        click.echo("Loading fixtures...")
        fixtures = get_fixtures()
        for item in fixtures:
            habit = Habit(**item["habit"])
            for comp_date in item["completions"]:
                habit.completions.append(Completion(completion_date=comp_date))
            db.add(habit)
        db.commit()
        click.secho("Demo database created and seeded successfully.", fg="green")
    finally:
        db.close()


@demo.command(name="reset")
def reset_demo():
    """Deletes the existing demo database."""
    demo_db_file = "demo_habits.db"
    if os.path.exists(demo_db_file):
        os.remove(demo_db_file)
        click.secho("Demo database has been reset.", fg="yellow")
        click.echo("Run 'habit demo start' to create a new one.")
    else:
        click.echo("No demo database found to reset.")


# --- Core Commands ---


@cli.command(name="list")
@click.option(
    "-p",
    "--periodicity",
    type=click.Choice(list(PERIODICITIES), case_sensitive=False),
    help="Filter habits by a specific periodicity.",
)
@click.pass_context
def list_habits(ctx: click.Context, periodicity: str):
    """A shortcut to display habits in a list format.

    Args:
        ctx (click.Context): The context object.
        periodicity (str): The optional period to filter by.
    """
    ctx.invoke(analyze, show="list", periodicity=periodicity)


@cli.command()
@click.argument("name")
@click.option(
    "-d", "--description", default="", help="A short description of the habit."
)
@click.option(
    "-p",
    "--periodicity",
    type=click.Choice(list(PERIODICITIES), case_sensitive=False),
    default="daily",
    help="The periodicity of the habit (daily, weekly, monthly).",
)
@click.pass_context
def add(ctx: click.Context, name: str, description: str, periodicity: str):
    """Adds a new habit to the database.

    Args:
        ctx (click.Context): The context object.
        name (str): The name of the new habit.
        description (str): An optional description for the habit.
        periodicity (str): The habit's period (daily, weekly, monthly).
    """
    Session = ctx.obj["session_factory"]
    db = Session()
    try:
        manager = HabitManager(db)
        if manager.find_by_name(name):
            click.secho(
                f"Error: A habit with the name '{name}' already exists.", fg="red"
            )
            return
        new_habit = Habit(
            name=name, description=description, periodicity=periodicity
        )
        manager.insert(new_habit)
        click.secho(
            f"Successfully added habit: '{name}' with {periodicity} periodicity.",
            fg="green",
        )
    finally:
        db.close()


@cli.command()
@click.argument("identifier")
@click.option("-n", "--new-name", help="A new name for the habit.")
@click.option("-d", "--description", help="A new description for the habit.")
@click.option(
    "-p",
    "--periodicity",
    type=click.Choice(list(PERIODICITIES), case_sensitive=False),
    help="A new periodicity for the habit.",
)
@click.pass_context
def update(
    ctx: click.Context,
    identifier: str,
    new_name: str,
    description: str,
    periodicity: str,
):
    """Updates an existing habit's attributes.

    Args:
        ctx (click.Context): The context object.
        identifier (str): The name or ID of the habit to update.
        new_name (str): An optional new name for the habit.
        description (str): An optional new description for the habit.
        periodicity (str): An optional new periodicity for the habit.
    """
    if not any([new_name, description, periodicity]):
        click.secho(
            "Error: Please provide at least one option to update.", fg="red"
        )
        return
    Session = ctx.obj["session_factory"]
    db = Session()
    try:
        manager = HabitManager(db)
        try:
            id_or_name = int(identifier)
        except ValueError:
            id_or_name = identifier
        if new_name and manager.find_by_name(new_name):
            click.secho(
                f"Error: A habit with the name '{new_name}' already exists.",
                fg="red",
            )
            return
        updated_habit = manager.update(
            id_or_name,
            new_name=new_name,
            new_description=description,
            new_periodicity=periodicity,
        )
        if updated_habit:
            click.secho(f"Successfully updated habit '{identifier}'.", fg="green")
        else:
            click.secho(f"Error: Habit '{identifier}' not found.", fg="red")
    except MultipleResultsFound:
        click.secho(
            f"Error: Multiple habits found with name '{identifier}'. Please update by ID.",
            fg="red",
        )
    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")
    finally:
        db.close()


@cli.command()
@click.argument("identifier")
@click.pass_context
def delete(ctx: click.Context, identifier: str):
    """Deletes a habit by its name or ID.

    Args:
        ctx (click.Context): The context object.
        identifier (str): The name or ID of the habit to delete.
    """
    Session = ctx.obj["session_factory"]
    db = Session()
    try:
        manager = HabitManager(db)
        try:
            id_or_name = int(identifier)
        except ValueError:
            id_or_name = identifier
        if manager.delete(id_or_name):
            click.secho(f"Successfully deleted habit '{identifier}'.", fg="green")
        else:
            click.secho(f"Error: Habit '{identifier}' not found.", fg="red")
    except MultipleResultsFound:
        click.secho(
            f"Error: Multiple habits found with name '{identifier}'. Please delete by ID.",
            fg="red",
        )
    finally:
        db.close()


@cli.command()
@click.argument("identifier")
@click.pass_context
def checkoff(ctx: click.Context, identifier: str):
    """Marks a habit as completed for the current time.

    Args:
        ctx (click.Context): The context object.
        identifier (str): The name or ID of the habit to complete.
    """
    Session = ctx.obj["session_factory"]
    db = Session()
    try:
        manager = HabitManager(db)
        try:
            id_or_name = int(identifier)
        except ValueError:
            id_or_name = identifier
        habit = manager.checkoff(id_or_name)
        if habit:
            click.secho(
                f"Successfully checked off habit: '{habit.name}'. Keep it up!",
                fg="green",
            )
        else:
            click.secho(f"Error: Habit '{identifier}' not found.", fg="red")
    except MultipleResultsFound:
        click.secho(
            f"Error: Multiple habits found with name '{identifier}'. Please checkoff by ID.",
            fg="red",
        )
    finally:
        db.close()


@cli.command()
@click.option(
    "-p",
    "--periodicity",
    type=click.Choice(list(PERIODICITIES), case_sensitive=False),
    help="Filter analysis by a specific periodicity.",
)
@click.option(
    "--show",
    type=click.Choice(
        ["table", "list", "summary", "streak", "struggle"], case_sensitive=False
    ),
    default="table",
    help="The type of analysis to show.",
)
@click.option("--habit", help="Specify a habit name or ID for streak analysis.")
@click.pass_context
def analyze(ctx: click.Context, periodicity: str, show: str, habit: str):
    """Analyzes and displays habit data.

    Args:
        ctx (click.Context): The context object.
        periodicity (str): An optional period to filter the analysis by.
        show (str): The type of analysis view to generate.
        habit (str): An optional habit identifier for streak analysis.
    """
    Session = ctx.obj["session_factory"]
    db = Session()
    try:
        if show == "table":
            click.echo(analysis.generate_table(db, periodicity=periodicity))
        elif show == "list":
            for item in analysis.generate_list(db, periodicity=periodicity):
                click.echo(f"- {item}")
        elif show == "summary":
            click.echo(analysis.generate_summary(db))
        elif show == "streak":
            if habit:
                try:
                    id_or_name = int(habit)
                except (ValueError, TypeError):
                    id_or_name = habit
                streak = analysis.longest_streak(db, identifier=id_or_name)
                click.echo(f"Longest streak for '{habit}': {streak} days")
            else:
                streak = analysis.longest_streak(db)
                click.echo(f"Longest streak across all habits: {streak} days")
        elif show == "struggle":
            results = analysis.struggled_habits(db)
            click.echo("--- Habit Struggle Score (Higher is worse) ---")
            for item in results:
                click.echo(
                    f"  - {item['habit'].name}: Score {item['score']} "
                    f"({item['breaks']} breaks, {item['gaps']} gap days)"
                )
    finally:
        db.close()


# Programmatically add all core commands to the 'demo' group.
# This avoids duplicating command definitions and ensures that any new
# command added to the main CLI is also available under 'demo'.
for command in [list_habits, add, update, delete, checkoff, analyze]:
    demo.add_command(command)
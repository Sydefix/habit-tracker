import click
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound

from .models import Base, Habit, Completion
from .habit_manager import HabitManager, PERIODICITIES
from . import analysis
from .fixtures import get_fixtures # Import our new fixtures

# --- Database Setup ---
# Production Database
PROD_DB_URL = "sqlite:///./production_habits.db"
PROD_ENGINE = create_engine(PROD_DB_URL, echo=False)
ProdSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=PROD_ENGINE)

# Demo Database
DEMO_DB_URL = "sqlite:///./demo_habits.db"
DEMO_ENGINE = create_engine(DEMO_DB_URL, echo=False)
DemoSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=DEMO_ENGINE)

# Ensure production tables are created
Base.metadata.create_all(bind=PROD_ENGINE)


# --- Click Command Group ---
@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.pass_context
def cli(ctx):
    """
    A Command-Line Interface for managing and analyzing habits.
    By default, commands run on the production database.
    Use the 'demo' command for a sandboxed environment.
    """
    # Store the production session factory in the context
    ctx.obj = {"session_factory": ProdSessionLocal}


# --- Demo Command Group ---
@cli.group()
@click.pass_context
def demo(ctx):
    """
    A playground to test habits using a separate demo database.

    First, run 'demo start' to create the environment.
    Then, run any command like 'demo list' or 'demo analyze'.
    """
    demo_db_file = "demo_habits.db"

    # If a user tries to run a command other than 'start' or 'reset'
    # and the DB doesn't exist, guide them.
    if (
        not os.path.exists(demo_db_file)
        and ctx.invoked_subcommand not in ["start", "reset"]
    ):
        click.secho("Error: Demo database not found.", fg="red")
        click.echo("Please run 'python cli.py demo start' to create it.")
        ctx.exit()  # Stop further execution

    # IMPORTANT: This switches the context for all subcommands of 'demo'
    ctx.obj["session_factory"] = DemoSessionLocal


@demo.command(name="start")
def start_demo():
    """Creates and seeds the demo database if it doesn't exist."""
    demo_db_file = "demo_habits.db"
    if os.path.exists(demo_db_file):
        click.echo("Demo database already exists.")
        click.echo(
            "You can continue using it, or run 'python cli.py demo reset' to start over."
        )
        return

    # Create tables and load fixtures
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
        click.echo("Run 'python cli.py demo start' to create a new one.")
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
def list_habits(ctx, periodicity: str):
    """A shortcut to display habits in a list format."""
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
def add(ctx, name: str, description: str, periodicity: str):
    """Adds a new habit to the database."""
    Session = ctx.obj["session_factory"]
    db = Session()
    try:
        manager = HabitManager(db)
        if manager.find_by_name(name):
            click.secho(f"Error: A habit with the name '{name}' already exists.", fg="red")
            return
        new_habit = Habit(name=name, description=description, periodicity=periodicity)
        manager.insert(new_habit)
        click.secho(f"Successfully added habit: '{name}' with {periodicity} periodicity.", fg="green")
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
def update(ctx, identifier: str, new_name: str, description: str, periodicity: str):
    """Updates an existing habit's attributes."""
    if not any([new_name, description, periodicity]):
        click.secho("Error: Please provide at least one option to update.", fg="red")
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
            click.secho(f"Error: A habit with the name '{new_name}' already exists.", fg="red")
            return
        updated_habit = manager.update(id_or_name, new_name=new_name, new_description=description, new_periodicity=periodicity)
        if updated_habit:
            click.secho(f"Successfully updated habit '{identifier}'.", fg="green")
        else:
            click.secho(f"Error: Habit '{identifier}' not found.", fg="red")
    except MultipleResultsFound:
        click.secho(f"Error: Multiple habits found with name '{identifier}'. Please update by ID.", fg="red")
    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")
    finally:
        db.close()


@cli.command()
@click.argument("identifier")
@click.pass_context
def delete(ctx, identifier: str):
    """Deletes a habit by its name or ID."""
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
        click.secho(f"Error: Multiple habits found with name '{identifier}'. Please delete by ID.", fg="red")
    finally:
        db.close()


@cli.command()
@click.argument("identifier")
@click.pass_context
def checkoff(ctx, identifier: str):
    """Marks a habit as completed for the current time."""
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
            click.secho(f"Successfully checked off habit: '{habit.name}'. Keep it up!", fg="green")
        else:
            click.secho(f"Error: Habit '{identifier}' not found.", fg="red")
    except MultipleResultsFound:
        click.secho(f"Error: Multiple habits found with name '{identifier}'. Please checkoff by ID.", fg="red")
    finally:
        db.close()


@cli.command()
@click.option("-p", "--periodicity", type=click.Choice(list(PERIODICITIES), case_sensitive=False), help="Filter analysis by a specific periodicity.")
@click.option("--show", type=click.Choice(["table", "list", "summary", "streak", "struggle"], case_sensitive=False), default="table", help="The type of analysis to show.")
@click.option("--habit", help="Specify a habit name or ID for streak analysis.")
@click.pass_context
def analyze(ctx, periodicity: str, show: str, habit: str):
    """Analyzes and displays habit data."""
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
                click.echo(f"  - {item['habit'].name}: Score {item['score']} ({item['breaks']} breaks, {item['gaps']} gap days)")
    finally:
        db.close()

# Dynamically add commands to the 'demo' group without rewriting function definitions
# This is why I chose Click, it is easy to do such a thing with it.
for command in [list_habits, add, update, delete, checkoff, analyze]:
    demo.add_command(command)

if __name__ == "__main__":
    cli()
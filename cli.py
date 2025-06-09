# cli.py

import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound

# Import the core components of our application
from models import Base, Habit
from habit_manager import HabitManager, PERIODICITIES
import analysis


# --- Database Setup ---
# This setup is consistent with other runnable scripts.
DATABASE_URL = "sqlite:///./production_habits.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure tables are created before any command runs
Base.metadata.create_all(bind=engine)


# --- Click Command Group ---
# This is the main entry point for all our commands.
@click.group()
def cli():
    """
    A Command-Line Interface for managing and analyzing habits.
    """
    pass


# --- Core Commands ---


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
def add(name: str, description: str, periodicity: str):
    """Adds a new habit to the database."""
    db = SessionLocal()
    try:
        manager = HabitManager(db)
        # Check if a habit with this name already exists
        if manager.find_by_name(name):
            click.secho(
                f"Error: A habit with the name '{name}' already exists.",
                fg="red",
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
def update(identifier: str, new_name: str, description: str, periodicity: str):
    """Updates an existing habit's attributes."""
    # Ensure at least one update option is provided
    if not any([new_name, description, periodicity]):
        click.secho(
            "Error: Please provide at least one option to update "
            "(--new-name, --description, or --periodicity).",
            fg="red",
        )
        click.echo("See 'python cli.py update --help' for more info.")
        return

    db = SessionLocal()
    try:
        manager = HabitManager(db)
        # Convert to int if possible, otherwise treat as string
        try:
            id_or_name = int(identifier)
        except ValueError:
            id_or_name = identifier

        # Prevent updating to a name that already exists
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
    except ValueError as e:  # Catches invalid periodicity from the manager
        click.secho(f"Error: {e}", fg="red")
    finally:
        db.close()


@cli.command()
@click.argument("identifier")
def delete(identifier: str):
    """Deletes a habit by its name or ID."""
    db = SessionLocal()
    try:
        manager = HabitManager(db)
        # Convert to int if possible, otherwise treat as string
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
def checkoff(identifier: str):
    """Marks a habit as completed for the current time."""
    db = SessionLocal()
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
        ["table", "list", "summary", "streak", "struggle"],
        case_sensitive=False,
    ),
    default="table",
    help="The type of analysis to show.",
)
@click.option(
    "--habit",
    help="Specify a habit name or ID for streak analysis.",
)
def analyze(periodicity: str, show: str, habit: str):
    """Analyzes and displays habit data."""
    db = SessionLocal()
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

@cli.command(name="list")
@click.option(
    "-p",
    "--periodicity",
    type=click.Choice(list(PERIODICITIES), case_sensitive=False),
    help="Filter habits by a specific periodicity.",
)
@click.pass_context
def list_habits(ctx, periodicity: str):
    """Display habits in a list format."""
    ctx.invoke(analyze, show="list", periodicity=periodicity)

if __name__ == "__main__":
    cli()
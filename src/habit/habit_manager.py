"""
Manages all persistence operations for Habit and Completion objects.

This module defines the HabitManager class, which acts as a business logic
layer, providing a clean interface for all CRUD (Create, Read, Update, Delete)
and other specific operations related to habits.
"""

from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from .models import Completion, Habit

PERIODICITIES = {"daily", "weekly", "monthly"}


class HabitManager:
    """A class to manage CRUD operations for Habit objects."""

    def __init__(self, session: Session):
        """Initializes the HabitManager with a database session.

        Args:
            session (Session): The SQLAlchemy session object to be used for
                all database operations.
        """
        self.session = session

    def find_by_name(self, name: str) -> Habit | None:
        """Finds a single habit by its unique name.

        Args:
            name (str): The exact name of the habit to find.

        Returns:
            Habit | None: The Habit object if exactly one is found, otherwise None.

        Raises:
            MultipleResultsFound: If more than one habit with the same name exists.
        """
        try:
            return self.session.query(Habit).filter(Habit.name == name).one()
        except NoResultFound:
            return None

    def find_by_id(self, habit_id: int) -> Habit | None:
        """Finds a single habit by its primary key (ID).

        Args:
            habit_id (int): The ID of the habit to find.

        Returns:
            Habit | None: The Habit object if found, otherwise None.
        """
        return self.session.get(Habit, habit_id)

    def find_habit(self, identifier: int | str) -> Habit | None:
        """Finds a habit by its ID or name.

        A wrapper for find_by_id and find_by_name to simplify workflows.

        Args:
            identifier (int | str): The ID (int) or name (str) of the habit.

        Returns:
            Habit | None: The Habit object if found, otherwise None.

        Raises:
            TypeError: If the identifier is not an integer or a string.
            MultipleResultsFound: If the identifier is a string and multiple
                habits match that name.
        """
        if isinstance(identifier, int):
            return self.find_by_id(identifier)
        elif isinstance(identifier, str):
            return self.find_by_name(identifier)
        else:
            raise TypeError(
                "Identifier must be an integer (ID) or a string (name)."
            )

    def get_all_habits(self) -> list[Habit]:
        """Retrieves all habits from the database.

        Returns:
            list[Habit]: A list of all Habit objects.
        """
        return self.session.query(Habit).all()

    def insert(self, habit_to_insert: Habit) -> Habit:
        """Inserts a new Habit object into the database.

        Args:
            habit_to_insert (Habit): The Habit instance to be saved.

        Returns:
            Habit: The saved Habit instance, refreshed with its new ID.

        Raises:
            ValueError: If the habit's periodicity is not one of the allowed values.
            SQLAlchemyError: If a database error occurs during the transaction.
        """
        if habit_to_insert.periodicity not in PERIODICITIES:
            raise ValueError(
                f"Invalid periodicity '{habit_to_insert.periodicity}'. "
                f"Allowed values: {PERIODICITIES}"
            )
        try:
            self.session.add(habit_to_insert)
            self.session.commit()
            self.session.refresh(habit_to_insert)
            return habit_to_insert
        except SQLAlchemyError:
            self.session.rollback()
            raise

    def update(
        self,
        identifier: int | str,
        new_name: str = None,
        new_description: str = None,
        new_periodicity: str = None,
    ) -> Habit | None:
        """Updates an existing habit's attributes.

        Args:
            identifier (int | str): The ID or name of the habit to update.
            new_name (str, optional): The new name for the habit.
            new_description (str, optional): The new description for the habit.
            new_periodicity (str, optional): The new periodicity for the habit.

        Returns:
            Habit | None: The updated Habit object if found and changed,
                otherwise None if the habit was not found.

        Raises:
            ValueError: If the new_periodicity is not one of the allowed values.
            MultipleResultsFound: If identifier is a string and multiple habits match.
            SQLAlchemyError: If a database error occurs during the transaction.
        """
        habit_to_update = self.find_habit(identifier)
        if not habit_to_update:
            return None

        updated_fields = False
        if new_name is not None and habit_to_update.name != new_name:
            habit_to_update.name = new_name
            updated_fields = True
        if (
            new_description is not None
            and habit_to_update.description != new_description
        ):
            habit_to_update.description = new_description
            updated_fields = True
        if new_periodicity is not None:
            if new_periodicity not in PERIODICITIES:
                raise ValueError(
                    f"Invalid periodicity '{new_periodicity}'. "
                    f"Allowed values: {PERIODICITIES}"
                )
            if habit_to_update.periodicity != new_periodicity:
                habit_to_update.periodicity = new_periodicity
                updated_fields = True

        if updated_fields:
            try:
                self.session.commit()
                self.session.refresh(habit_to_update)
            except SQLAlchemyError:
                self.session.rollback()
                raise
        return habit_to_update

    def delete(self, identifier: int | str) -> bool:
        """Deletes a habit from the database by its name or ID.

        Args:
            identifier (int | str): The name or ID of the habit to delete.

        Returns:
            bool: True if the habit was found and deleted, False otherwise.

        Raises:
            MultipleResultsFound: If identifier is a string and multiple habits match.
            SQLAlchemyError: If a database error occurs during the transaction.
        """
        habit_to_delete = self.find_habit(identifier)
        if not habit_to_delete:
            return False
        try:
            self.session.delete(habit_to_delete)
            self.session.commit()
            return True
        except SQLAlchemyError:
            self.session.rollback()
            raise

    def checkoff(self, identifier: int | str) -> Habit | None:
        """Marks a habit as completed for the current time.

        This is done by creating and saving a new Completion record associated
        with the specified habit.

        Args:
            identifier (int | str): The name or ID of the habit to check off.

        Returns:
            Habit | None: The Habit object, refreshed with the new completion,
                or None if the habit was not found.

        Raises:
            MultipleResultsFound: If identifier is a string and multiple habits match.
            SQLAlchemyError: If a database error occurs during the transaction.
        """
        habit_to_checkoff = self.find_habit(identifier)
        if not habit_to_checkoff:
            return None
        try:
            new_completion = Completion(completion_date=datetime.now())
            habit_to_checkoff.completions.append(new_completion)
            self.session.commit()
            self.session.refresh(habit_to_checkoff)
            return habit_to_checkoff
        except SQLAlchemyError:
            self.session.rollback()
            raise
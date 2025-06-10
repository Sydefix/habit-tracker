from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.exc import SQLAlchemyError
from .models import Habit, Completion
from datetime import datetime

PERIODICITIES = {"daily", "weekly", "monthly"}

class HabitManager:
    
    def __init__(self, session):
        self.session = session
    
    
    session: None

    def find_by_name(self, name: str) -> Habit | None:
        """
        Run select query with name as condition.
        Returns the Habit object if exactly one is found.
        """
        try:
            habit = self.session.query(Habit).filter(Habit.name == name).one()
            return habit
        except NoResultFound:
            return None

    def find_by_id(self, habit_id: int) -> Habit | None:
        """
        run select query with ID as condition and return result, 
        it must return only one
        """
        return self.session.get(Habit, habit_id)

    def find_habit(self, identifier: int | str) -> Habit | None:        
        """
        a wrapper for findbyName and FindbyID to simplify the workflow and testing
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
        """
        Retrieves all habits from the database.
        """
        return self.session.query(Habit).all()
    
    def insert(self, habit_to_insert: Habit) -> Habit:
        
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
        habit_to_update = self.find_habit(identifier)
        if not habit_to_update:
            return None

        updated_fields = False
        if new_name is not None and habit_to_update.name != new_name:
            habit_to_update.name = new_name
            updated_fields = True
        if new_description is not None and habit_to_update.description != new_description:
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
        return habit_to_update if habit_to_update else None

    def delete(self, identifier: int | str) -> bool:
        """
        remove an object from database by name or ID
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
        """
        update the status into checkoff 
        but it will also add current time into database list
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
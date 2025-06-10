from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import MultipleResultsFound
from datetime import datetime
from typing import Iterator
from habit.habit_manager import HabitManager

from habit.models import Base, Habit, Completion # Completion might be used if testing insert with completions

import pytest

# --- Helper function to add a habit for tests ---
def _add_habit(
    session: SQLAlchemySession,
    name: str,
    description: str = "Test Description",
    creation_date: datetime = None,
    periodicity: str = "daily", 
) -> Habit:
    if creation_date is None:
        creation_date = datetime.now()
    habit = Habit(
        name=name,
        description=description,
        creation_date=creation_date,
        periodicity=periodicity,
    )
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


# --- Test Cases ---

def test_insert_habit(habit_manager: HabitManager, db_session: SQLAlchemySession):
    habit_name = "Morning Meditation"
    description = "10 minutes of guided meditation."
    periodicity = "daily"
    new_habit = Habit(name=habit_name, description=description, periodicity=periodicity )
    inserted_habit = habit_manager.insert(new_habit)
    assert inserted_habit is not None
    assert inserted_habit.id is not None
    assert inserted_habit.name == habit_name
    retrieved_habit = (
        db_session.query(Habit).filter(Habit.id == inserted_habit.id).one()
    )
    assert retrieved_habit == inserted_habit

def test_insert_habit_with_completions(
    habit_manager: HabitManager, db_session: SQLAlchemySession
):
    """Test inserting a habit that already has completion objects associated."""
    habit_name = "Evening Walk"
    new_habit = Habit(name=habit_name, description="30-minute walk.", periodicity="daily")
    completion1 = Completion(completion_date=datetime(2025, 5, 20, 18, 0, 0))
    completion2 = Completion(completion_date=datetime(2025, 5, 21, 18, 30, 0))
    new_habit.completions.extend([completion1, completion2])

    inserted_habit = habit_manager.insert(new_habit)
    db_session.refresh(inserted_habit) # Ensure relationships are loaded

    assert inserted_habit is not None
    assert inserted_habit.id is not None
    assert len(inserted_habit.completions) == 2
    assert inserted_habit.completions[0].id is not None # Completions get IDs
    assert inserted_habit.completions[0].habit_id == inserted_habit.id

def test_insert_invalid_periodicity(habit_manager, db_session):
    
    habit = Habit(name="Test", description="desc", periodicity="yearly")
    with pytest.raises(ValueError):
        habit_manager.insert(habit)

def test_find_by_id_existing(
    habit_manager: HabitManager, db_session: SQLAlchemySession
):
    added_habit = _add_habit(db_session, "Read a Chapter")
    found_habit = habit_manager.find_by_id(added_habit.id)
    assert found_habit is not None
    assert found_habit.id == added_habit.id
    assert found_habit.name == "Read a Chapter"


def test_find_by_id_non_existing(habit_manager: HabitManager):
    non_existent_id = 99999
    found_habit = habit_manager.find_by_id(non_existent_id)
    assert found_habit is None


def test_find_by_name_existing(
    habit_manager: HabitManager, db_session: SQLAlchemySession
):
    habit_name = "Daily Journaling"
    added_habit = _add_habit(db_session, habit_name)
    found_habit = habit_manager.find_by_name(habit_name)
    assert found_habit is not None
    assert found_habit.name == habit_name
    assert found_habit.id == added_habit.id


def test_find_by_name_non_existing(habit_manager: HabitManager):
    non_existent_name = "Teleport to Work"
    found_habit = habit_manager.find_by_name(non_existent_name)
    assert found_habit is None


def test_find_by_name_multiple_results(
    habit_manager: HabitManager, db_session: SQLAlchemySession
):
    habit_name = "Drink Water"
    _add_habit(db_session, habit_name, "First reminder")
    _add_habit(db_session, habit_name, "Second reminder")
    with pytest.raises(MultipleResultsFound):
        habit_manager.find_by_name(habit_name)


# --- Tests for find_habit wrapper ---

def test_find_habit_with_existing_id(
    habit_manager: HabitManager, db_session: SQLAlchemySession
):
    added_habit = _add_habit(db_session, "Stretch")
    found_habit = habit_manager.find_habit(added_habit.id)
    assert found_habit is not None
    assert found_habit.id == added_habit.id


def test_find_habit_with_non_existing_id(habit_manager: HabitManager):
    found_habit = habit_manager.find_habit(99998)
    assert found_habit is None


def test_find_habit_with_existing_name(
    habit_manager: HabitManager, db_session: SQLAlchemySession
):
    habit_name = "Plan the Day"
    added_habit = _add_habit(db_session, habit_name)
    found_habit = habit_manager.find_habit(habit_name)
    assert found_habit is not None
    assert found_habit.name == habit_name


def test_find_habit_with_non_existing_name(habit_manager: HabitManager):
    found_habit = habit_manager.find_habit("Invent a Gadget")
    assert found_habit is None


def test_find_by_name_multiple_results(habit_manager, db_session: SQLAlchemySession):
    habit_name = "Drink Water"
    _add_habit(db_session, habit_name, "First reminder")
    _add_habit(db_session, habit_name, "Second reminder")
    with pytest.raises(MultipleResultsFound):
        habit_manager.find_by_name(habit_name)

def test_find_habit_with_invalid_identifier_type(habit_manager: HabitManager):
    with pytest.raises(TypeError):
        habit_manager.find_habit(123.45)
    with pytest.raises(TypeError):
        habit_manager.find_habit([123])


# --- Test for get_all_habits ---

def test_get_all_habits_empty(habit_manager: HabitManager):
    """Test get_all_habits when no habits are in the database."""
    all_habits = habit_manager.get_all_habits()
    assert len(all_habits) == 0
    assert all_habits == []


def test_get_all_habits_with_data(
    habit_manager: HabitManager, db_session: SQLAlchemySession
):
    """Test get_all_habits when there are habits in the database."""
    habit1 = _add_habit(db_session, "Habit Alpha")
    habit2 = _add_habit(db_session, "Habit Beta")

    all_habits = habit_manager.get_all_habits()
    assert len(all_habits) == 2

    # Check if the retrieved habits match the ones added
    # Order might not be guaranteed unless explicitly ordered in the query
    retrieved_ids = sorted([h.id for h in all_habits])
    expected_ids = sorted([habit1.id, habit2.id])
    assert retrieved_ids == expected_ids

    retrieved_names = sorted([h.name for h in all_habits])
    expected_names = sorted([habit1.name, habit2.name])
    assert retrieved_names == expected_names
    

# --- Tests for update method ---

def test_update_habit_by_id(
    habit_manager: HabitManager, db_session: SQLAlchemySession
):
    """Test updating a habit's name and description by its ID."""
    original_name = "Initial Name"
    original_desc = "Initial Description"
    habit = _add_habit(db_session, original_name, original_desc)

    new_name = "Updated Name by ID"
    new_desc = "Updated Description by ID"
    updated_habit = habit_manager.update(
        habit.id, new_name=new_name, new_description=new_desc
    )

    assert updated_habit is not None
    assert updated_habit.id == habit.id
    assert updated_habit.name == new_name
    assert updated_habit.description == new_desc

    # Verify in DB
    refreshed_habit = db_session.get(Habit, habit.id)
    assert refreshed_habit.name == new_name
    assert refreshed_habit.description == new_desc



def test_update_habit_by_name(
    habit_manager: HabitManager, db_session: SQLAlchemySession
):
    """Test updating a habit's description by its name."""
    original_name = "Name To Update"
    original_desc = "Original Desc"
    habit = _add_habit(db_session, original_name, original_desc)

    new_desc = "Updated Description by Name"
    updated_habit = habit_manager.update(
        original_name, new_description=new_desc
    )

    assert updated_habit is not None
    assert updated_habit.id == habit.id
    assert updated_habit.name == original_name # Name was not changed
    assert updated_habit.description == new_desc


def test_update_habit_no_changes(
    habit_manager: HabitManager, db_session: SQLAlchemySession
):
    """Test update when no actual changes are made to the data."""
    name = "No Change Habit"
    desc = "No Change Desc"
    habit = _add_habit(db_session, name, desc)

    # Call update with the same data or no data
    updated_habit_same_data = habit_manager.update(
        habit.id, new_name=name, new_description=desc
    )
    assert updated_habit_same_data is not None # Returns the habit
    assert updated_habit_same_data.name == name
    assert updated_habit_same_data.description == desc

    updated_habit_no_args = habit_manager.update(habit.id)
    assert updated_habit_no_args is not None # Returns the habit
    assert updated_habit_no_args.name == name


def test_update_non_existent_habit(habit_manager: HabitManager):
    """Test updating a habit that does not exist."""
    result_by_id = habit_manager.update(9999, new_name="Ghost Habit")
    assert result_by_id is None

    result_by_name = habit_manager.update(
        "Ghost Habit Name", new_name="Ghost Habit"
    )
    assert result_by_name is None


def test_update_habit_by_name_multiple_results(
    habit_manager: HabitManager, db_session: SQLAlchemySession
):
    """Test update by name when multiple habits share the same name."""
    shared_name = "Shared Update Name"
    _add_habit(db_session, shared_name, "Instance 1")
    _add_habit(db_session, shared_name, "Instance 2")

    with pytest.raises(MultipleResultsFound):
        habit_manager.update(shared_name, new_description="New Shared Desc")


def test_update_invalid_periodicity(habit_manager, db_session):
    habit = _add_habit(db_session, "Test", "desc", periodicity="daily")
    with pytest.raises(ValueError):
        habit_manager.update(habit.id, new_periodicity="yearly")

# --- Tests for delete method ---

def test_delete_habit_by_id(
    habit_manager: HabitManager, db_session: SQLAlchemySession
):
    """Test deleting a habit by its ID."""
    habit_to_delete = _add_habit(db_session, "Delete Me By ID")
    habit_id = habit_to_delete.id

    # Add a completion to test cascade delete
    completion = Completion(completion_date=datetime.now(), habit_id=habit_id)
    db_session.add(completion)
    db_session.commit()
    completion_id = completion.id

    assert db_session.get(Habit, habit_id) is not None
    assert db_session.get(Completion, completion_id) is not None

    delete_result = habit_manager.delete(habit_id)
    assert delete_result is True
    assert db_session.get(Habit, habit_id) is None
    assert db_session.get(Completion, completion_id) is None # Verifies cascade


def test_delete_habit_by_name(
    habit_manager: HabitManager, db_session: SQLAlchemySession
):
    """Test deleting a habit by its name."""
    habit_name = "Delete Me By Name"
    habit_to_delete = _add_habit(db_session, habit_name)
    habit_id = habit_to_delete.id # Get ID for verification

    assert db_session.get(Habit, habit_id) is not None
    delete_result = habit_manager.delete(habit_name)
    assert delete_result is True
    assert db_session.get(Habit, habit_id) is None


def test_delete_non_existent_habit(habit_manager: HabitManager):
    """Test deleting a habit that does not exist."""
    delete_result_by_id = habit_manager.delete(8888)
    assert delete_result_by_id is False

    delete_result_by_name = habit_manager.delete("Non Existent Delete Name")
    assert delete_result_by_name is False


def test_delete_habit_by_name_multiple_results(
    habit_manager: HabitManager, db_session: SQLAlchemySession
):
    """Test delete by name when multiple habits share the same name."""
    shared_name = "Shared Delete Name"
    _add_habit(db_session, shared_name, "Delete Instance 1")
    _add_habit(db_session, shared_name, "Delete Instance 2")

    with pytest.raises(MultipleResultsFound):
        habit_manager.delete(shared_name)

# --- Tests for checkoff method ---

def test_checkoff_habit_by_id(
    habit_manager: HabitManager, db_session: SQLAlchemySession
):
    """Test checking off a habit by its ID."""
    habit = _add_habit(db_session, "Morning Run")
    # Ensure completions list is loaded before modification, or check count after.
    db_session.refresh(habit) # Good practice to have the fresh state
    initial_completion_count = len(habit.completions)

    checked_off_habit = habit_manager.checkoff(habit.id)

    assert checked_off_habit is not None
    assert checked_off_habit.id == habit.id
    assert len(checked_off_habit.completions) == initial_completion_count + 1

    # Verify the new completion details
    new_completion = checked_off_habit.completions[-1] # Assumes it's the last one
    assert new_completion.id is not None
    assert new_completion.habit_id == habit.id
    assert (
        datetime.now() - new_completion.completion_date
    ).total_seconds() < 5  # Check if timestamp is recent


def test_checkoff_habit_by_name(
    habit_manager: HabitManager, db_session: SQLAlchemySession
):
    """Test checking off a habit by its name."""
    habit_name = "Read a Book Daily"
    habit = _add_habit(db_session, habit_name)
    db_session.refresh(habit)
    initial_completion_count = len(habit.completions)

    checked_off_habit = habit_manager.checkoff(habit_name)

    assert checked_off_habit is not None
    assert checked_off_habit.name == habit_name
    assert len(checked_off_habit.completions) == initial_completion_count + 1
    new_completion = checked_off_habit.completions[-1]
    assert new_completion.habit_id == checked_off_habit.id
    assert (
        datetime.now() - new_completion.completion_date
    ).total_seconds() < 5


def test_checkoff_non_existent_habit(habit_manager: HabitManager):
    """Test checking off a habit that does not exist."""
    result_by_id = habit_manager.checkoff(77777) # Non-existent ID
    assert result_by_id is None

    result_by_name = habit_manager.checkoff("Ghost Habit for Checkoff")
    assert result_by_name is None


def test_checkoff_habit_by_name_multiple_results(
    habit_manager: HabitManager, db_session: SQLAlchemySession
):
    """Test checkoff by name when multiple habits share the same name."""
    shared_name = "Shared Habit Name for Checkoff"
    _add_habit(db_session, shared_name, "Instance A")
    _add_habit(db_session, shared_name, "Instance B")

    with pytest.raises(MultipleResultsFound):
        habit_manager.checkoff(shared_name)


def test_checkoff_multiple_times(
    habit_manager: HabitManager, db_session: SQLAlchemySession
):
    """Test checking off the same habit multiple times, creating multiple completions."""
    habit = _add_habit(db_session, "Daily Water Intake")
    db_session.refresh(habit)

    # First checkoff
    checked_off_habit_1 = habit_manager.checkoff(habit.id)
    assert checked_off_habit_1 is not None
    assert len(checked_off_habit_1.completions) == 1
    first_completion_time = checked_off_habit_1.completions[0].completion_date

    # Simulate a small delay if needed for timestamp comparison, though not strictly required
    # import time
    # time.sleep(0.01)

    # Second checkoff
    checked_off_habit_2 = habit_manager.checkoff(habit.id)
    assert checked_off_habit_2 is not None
    # After refresh, the habit object from the first checkoff might be stale
    # if not the same instance. It's better to check the length on the newly returned object.
    assert len(checked_off_habit_2.completions) == 2
    second_completion_time = checked_off_habit_2.completions[1].completion_date

    assert second_completion_time >= first_completion_time # Should be greater or equal
    # To be more precise, ensure they are distinct objects if IDs are different
    assert checked_off_habit_2.completions[0].id != checked_off_habit_2.completions[1].id


# main.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Assuming models.py and habit_manager.py are in the same directory
from models import Base, Habit, Completion
from habit_manager import HabitManager
from sqlalchemy.orm.exc import MultipleResultsFound


# --- Database Setup ---
# Using an in-memory SQLite database for easy testing
# For a persistent database, use a file path: "sqlite:///./habits.db"
DATABASE_URL = "sqlite:///:memory:"
# DATABASE_URL = "sqlite:///./test_habits.db" # Or a file-based DB

engine = create_engine(DATABASE_URL, echo=False)  # Set echo=True for SQL logging

# Create tables defined in models.py
Base.metadata.create_all(bind=engine)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def run_tests():
    # Create a new database session
    db_session = SessionLocal()

    # Instantiate HabitManager
    manager = HabitManager(session=db_session)

    print("--- Testing Habit Insertion ---")
    habit_name_1 = "Read a Book"
    new_habit_1 = Habit(
        name=habit_name_1, description="Read at least 20 pages of a book."
    )

    try:
        inserted_habit_1 = manager.insert(new_habit_1)
        if inserted_habit_1:
            print(
                f"Habit '{inserted_habit_1.name}' inserted with ID: {inserted_habit_1.id}"
            )
            print(f"Creation date: {inserted_habit_1.creation_date}")
        else:
            print(f"Failed to insert habit '{habit_name_1}'.")

    except Exception as e:
        print(f"An error occurred during insertion of '{habit_name_1}': {e}")

    print("\n--- Testing Find by Name (Existing Habit) ---")
    try:
        found_habit = manager.find_by_name(habit_name_1)
        if found_habit:
            print(f"Found habit: {found_habit}")
        else:
            print(f"Habit '{habit_name_1}' not found after insertion (unexpected).")
    except MultipleResultsFound:
        print(f"Error: Multiple habits found for '{habit_name_1}'. This is unexpected.")
    except Exception as e:
        print(f"An error occurred while finding '{habit_name_1}': {e}")

    print("\n--- Testing Find by Name (Non-Existing Habit) ---")
    non_existent_name = "Fly to Mars"
    try:
        found_non_existent = manager.find_by_name(non_existent_name)
        if found_non_existent:
            print(
                f"Found habit '{non_existent_name}' but it should not exist (unexpected)."
            )
        else:
            print(f"Habit '{non_existent_name}' correctly not found.")
    except Exception as e:
        print(f"An error occurred while finding '{non_existent_name}': {e}")

    print("\n--- Testing Insertion of a Habit with Completions (Illustrative) ---")
    habit_name_2 = "Morning Exercise"
    new_habit_2 = Habit(
        name=habit_name_2, description="30 minutes of cardio."
    )
    # Add completions (though HabitManager.insert doesn't directly handle this,
    # the relationship is defined in models.py)
    completion1 = Completion(completion_date=datetime(2025, 5, 27, 8, 0, 0))
    completion2 = Completion(completion_date=datetime(2025, 5, 28, 8, 15, 0))
    new_habit_2.completions.append(completion1)
    new_habit_2.completions.append(completion2)

    try:
        inserted_habit_2 = manager.insert(new_habit_2)
        if inserted_habit_2:
            print(
                f"Habit '{inserted_habit_2.name}' inserted with ID: {inserted_habit_2.id}"
            )
            # Verify completions were cascaded
            db_session.refresh(inserted_habit_2) # Ensure completions are loaded
            if inserted_habit_2.completions:
                print(f"  Completions for '{inserted_habit_2.name}':")
                for comp in inserted_habit_2.completions:
                    print(f"    - ID: {comp.id}, Date: {comp.completion_date}")
            else:
                print(f"  No completions found for '{inserted_habit_2.name}' after insert.")

    except Exception as e:
        print(f"An error occurred during insertion of '{habit_name_2}': {e}")


    print("\n--- Testing Duplicate Name Insertion (Illustrative) ---")
    # This will likely succeed unless you have a UNIQUE constraint on Habit.name
    # or add pre-check logic in HabitManager.insert
    duplicate_habit = Habit(name=habit_name_1, description="Another read a book habit")
    try:
        inserted_duplicate = manager.insert(duplicate_habit)
        if inserted_duplicate:
            print(f"Inserted duplicate named habit with new ID: {inserted_duplicate.id}")
            # Now, find_by_name might cause issues if not handled
            try:
                manager.find_by_name(habit_name_1)
            except MultipleResultsFound:
                print(f"As expected, MultipleResultsFound for name '{habit_name_1}' after duplicate insert.")
    except Exception as e:
        print(f"Error inserting duplicate habit: {e}")


    # Close the session
    db_session.close()
    print("\n--- Tests Finished. Session closed. ---")


if __name__ == "__main__":
    run_tests()
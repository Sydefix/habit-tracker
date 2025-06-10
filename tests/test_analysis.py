from datetime import datetime, timedelta
import pytest
from sqlalchemy.orm import Session as SQLAlchemySession

from habit.models import Habit, Completion
from habit.analysis import (
    _calculate_current_deadline,
    _periodicity,
    generate_summary,
    generate_table,
    generate_list,
    longest_streak,
    _break_count,
    _gap_count,
    _gap_days,
    struggled_habits,
)


# --- Helper Functions ---

def _add_habit(
    session: SQLAlchemySession,
    name: str,
    periodicity: str,
    creation_date: datetime = None,
    description: str = "Test Desc",
) -> Habit:
    """Helper to add a habit for testing."""
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


class MockHabit:
    """A non-DB mock for testing the pure deadline calculation function."""

    def __init__(self, periodicity):
        self.periodicity = periodicity


# --- Test Cases ---


def test_calculate_deadline_daily():
    habit = MockHabit(periodicity="daily")
    now = datetime(2025, 6, 11, 15, 30)  # A Wednesday
    deadline = _calculate_current_deadline(habit, now)
    assert deadline.year == 2025
    assert deadline.month == 6
    assert deadline.day == 11
    assert deadline.hour == 23
    assert deadline.minute == 59


def test_calculate_deadline_weekly():
    habit = MockHabit(periodicity="weekly")
    now = datetime(2025, 6, 11, 15, 30)  # A Wednesday
    deadline = _calculate_current_deadline(habit, now)
    assert deadline.year == 2025
    assert deadline.month == 6
    assert deadline.day == 15  # The upcoming Sunday
    assert deadline.hour == 23


def test_calculate_deadline_monthly():
    habit = MockHabit(periodicity="monthly")
    now = datetime(2025, 6, 11, 15, 30)  # June has 30 days
    deadline = _calculate_current_deadline(habit, now)
    assert deadline.year == 2025
    assert deadline.month == 6
    assert deadline.day == 30
    assert deadline.hour == 23


def test_filter_by_periodicity(db_session: SQLAlchemySession):
    _add_habit(db_session, "Daily Habit", "daily")
    _add_habit(db_session, "Weekly Habit 1", "weekly")
    _add_habit(db_session, "Weekly Habit 2", "weekly")

    daily_habits = _periodicity(db_session, "daily")
    assert len(daily_habits) == 1
    assert daily_habits[0].name == "Daily Habit"

    weekly_habits = _periodicity(db_session, "weekly")
    assert len(weekly_habits) == 2

    monthly_habits = _periodicity(db_session, "monthly")
    assert len(monthly_habits) == 0


def test_generate_table_all(db_session: SQLAlchemySession):
    _add_habit(db_session, "Habit One", "daily")
    _add_habit(db_session, "Habit Two", "weekly")

    table_str = generate_table(db_session)
    assert "Habit One" in table_str
    assert "Habit Two" in table_str
    assert "Status" in table_str and "Deadline" in table_str


def test_generate_table_filtered_by_periodicity(db_session: SQLAlchemySession):
    _add_habit(db_session, "Daily Task", "daily")
    _add_habit(db_session, "Weekly Task", "weekly")

    table_str = generate_table(db_session, periodicity="weekly")
    assert "Weekly Task" in table_str
    assert "Daily Task" not in table_str


def test_generate_table_with_pre_supplied_list(db_session: SQLAlchemySession):
    h1 = _add_habit(db_session, "List Habit 1", "daily")
    _add_habit(db_session, "List Habit 2", "daily")  # This one won't be passed

    table_str = generate_table(db_session, habits=[h1])
    assert "List Habit 1" in table_str
    assert "List Habit 2" not in table_str


def test_generate_list_all(db_session: SQLAlchemySession):
    _add_habit(db_session, "My Daily Habit", "daily")
    _add_habit(db_session, "My Weekly Habit", "weekly")

    result_list = generate_list(db_session)
    assert len(result_list) == 2
    assert any("My Daily Habit" in s for s in result_list)
    assert any("My Weekly Habit" in s for s in result_list)
    assert "The deadline is" in result_list[0]


def test_generate_list_filtered_by_periodicity(db_session: SQLAlchemySession):
    _add_habit(db_session, "A Daily Thing", "daily")
    _add_habit(db_session, "A Weekly Thing", "weekly")

    result_list = generate_list(db_session, periodicity="daily")
    assert len(result_list) == 1
    assert "A Daily Thing" in result_list[0]


def test_status_check_in_generation(db_session: SQLAlchemySession):
    """Tests if the status icon (☑/☐) is correct."""
    h_checked = _add_habit(db_session, "Checked Habit", "daily")
    h_unchecked = _add_habit(db_session, "Unchecked Habit", "daily")

    # Add a completion to the first habit
    h_checked.completions.append(Completion(completion_date=datetime.now()))
    db_session.commit()

    table_str = generate_table(db_session)
    list_result = generate_list(db_session)

    # Split the table into individual lines
    table_lines = table_str.split('\n')

    # Find the specific line for each habit
    checked_line = next(
        (line for line in table_lines if "Checked Habit" in line), None
    )
    unchecked_line = next(
        (line for line in table_lines if "Unchecked Habit" in line), None
    )

    # Assert that the line exists and starts with the correct symbol
    assert checked_line is not None
    assert checked_line.strip().startswith("☑")

    assert unchecked_line is not None
    assert unchecked_line.strip().startswith("☐")

    # --- Assertions for the list (these were already correct) ---
    assert any(s.startswith("☑ Checked Habit") for s in list_result)
    assert any(s.startswith("☐ Unchecked Habit") for s in list_result)
    

def test_longest_streak_no_completions(db_session: SQLAlchemySession):
    """Test streak calculation when a habit has no completions."""
    _add_habit(db_session, "Empty Habit", "daily")
    assert longest_streak(db_session, identifier="Empty Habit") == 0


def test_longest_streak_single_completion(db_session: SQLAlchemySession):
    """Test streak calculation for a single completion (streak of 1)."""
    habit = _add_habit(db_session, "Single Day Habit", "daily")
    habit.completions.append(Completion(completion_date=datetime.now()))
    db_session.commit()
    assert longest_streak(db_session, identifier=habit.id) == 1


def test_longest_streak_consecutive_days(db_session: SQLAlchemySession):
    """Test a simple consecutive streak."""
    habit = _add_habit(db_session, "Consecutive Habit", "daily")
    now = datetime.now()
    habit.completions.extend([
        Completion(completion_date=now - timedelta(days=2)),
        Completion(completion_date=now - timedelta(days=1)),
        Completion(completion_date=now),
    ])
    db_session.commit()
    assert longest_streak(db_session, identifier=habit.id) == 3


def test_longest_streak_non_consecutive_days(db_session: SQLAlchemySession):
    """Test that a gap in days results in a streak of 1."""
    habit = _add_habit(db_session, "Gapped Habit", "daily")
    now = datetime.now()
    habit.completions.extend([
        Completion(completion_date=now - timedelta(days=5)),
        Completion(completion_date=now - timedelta(days=1)),
    ])
    db_session.commit()
    assert longest_streak(db_session, identifier=habit.id) == 1


def test_longest_streak_multiple_completions_same_day(
    db_session: SQLAlchemySession,
):
    """Test that multiple checkoffs on the same day don't inflate the streak."""
    habit = _add_habit(db_session, "Multi-Checkoff Habit", "daily")
    now = datetime.now()
    habit.completions.extend([
        Completion(completion_date=now - timedelta(days=1)),
        Completion(completion_date=now.replace(hour=9)), # Today
        Completion(completion_date=now.replace(hour=17)), # Also today
    ])
    db_session.commit()
    assert longest_streak(db_session, identifier=habit.id) == 2


def test_longest_streak_broken_streak(db_session: SQLAlchemySession):
    """Test finding the longer of two separate streaks."""
    habit = _add_habit(db_session, "Broken Streak Habit", "daily")
    now = datetime.now()
    habit.completions.extend([
        Completion(completion_date=now - timedelta(days=10)), # Streak 1
        Completion(completion_date=now - timedelta(days=9)),
        Completion(completion_date=now - timedelta(days=5)), # Streak 2
        Completion(completion_date=now - timedelta(days=4)),
        Completion(completion_date=now - timedelta(days=3)),
    ])
    db_session.commit()
    # The longest streak is the second one, with a length of 3
    assert longest_streak(db_session, identifier=habit.id) == 3


def test_longest_streak_all_habits(db_session: SQLAlchemySession):
    """Test finding the longest streak among all habits."""
    # Habit A has a streak of 2
    habit_a = _add_habit(db_session, "Habit A", "daily")
    now = datetime.now()
    habit_a.completions.extend([
        Completion(completion_date=now - timedelta(days=1)),
        Completion(completion_date=now),
    ])

    # Habit B has a streak of 4
    habit_b = _add_habit(db_session, "Habit B", "daily")
    habit_b.completions.extend([
        Completion(completion_date=now - timedelta(days=3)),
        Completion(completion_date=now - timedelta(days=2)),
        Completion(completion_date=now - timedelta(days=1)),
        Completion(completion_date=now),
    ])
    db_session.commit()

    # When checking all habits, it should return the longest one (4)
    assert longest_streak(db_session) == 4


def test_longest_streak_non_existent_habit(db_session: SQLAlchemySession):
    """Test that a non-existent identifier returns a streak of 0."""
    assert longest_streak(db_session, identifier=99999) == 0
    assert longest_streak(db_session, identifier="Ghost Habit") == 0

def test_break_count(db_session: SQLAlchemySession):
    """Test the _break_count helper function."""
    habit = _add_habit(db_session, "Break Test Habit", "daily")
    now = datetime.now()
    
    # No breaks
    assert _break_count(habit) == 0
    
    # Add a consecutive streak (still no breaks)
    habit.completions.extend([
        Completion(completion_date=now - timedelta(days=2)),
        Completion(completion_date=now - timedelta(days=1)),
    ])
    db_session.commit()
    assert _break_count(habit) == 0
    
    # Add one break
    habit.completions.append(Completion(completion_date=now - timedelta(days=5)))
    db_session.commit()
    assert _break_count(habit) == 1
    
    # Add a second break
    habit.completions.append(Completion(completion_date=now - timedelta(days=10)))
    db_session.commit()
    assert _break_count(habit) == 2


def test_gap_count(db_session: SQLAlchemySession):
    """Test the _gap_count helper function."""
    habit = _add_habit(db_session, "Gap Test Habit", "daily")
    now = datetime.now()
    
    # No gaps
    assert _gap_count(habit) == 0
    
    # Gap of 2 days (between day 3 and day 6)
    habit.completions.extend([
        Completion(completion_date=now - timedelta(days=6)),
        Completion(completion_date=now - timedelta(days=3)),
    ])
    db_session.commit()
    assert _gap_count(habit) == 2 # Missed day 5 and day 4
    
    # Add another gap of 1 day (between day 1 and day 3)
    habit.completions.append(Completion(completion_date=now - timedelta(days=1)))
    db_session.commit()
    assert _gap_count(habit) == 3 # 2 from before + 1 new one (day 2)


def test_gap_days(db_session: SQLAlchemySession):
    """Test the _gap_days helper function."""
    habit = _add_habit(db_session, "Gap Days Test Habit", "daily")
    now = datetime.now().date()
    
    # No gaps
    assert _gap_days(habit) == {"break_dates": [], "resume_dates": []}
    
    # Add completions with gaps
    habit.completions.extend([
        Completion(completion_date=now - timedelta(days=10)), # End of streak 1
        Completion(completion_date=now - timedelta(days=7)),  # Start of streak 2
        Completion(completion_date=now - timedelta(days=6)),  # End of streak 2
        Completion(completion_date=now - timedelta(days=2)),  # Start of streak 3
    ])
    db_session.commit()
    
    result = _gap_days(habit)
    expected_breaks = [now - timedelta(days=10), now - timedelta(days=6)]
    expected_resumes = [now - timedelta(days=7), now - timedelta(days=2)]
    
    assert result["break_dates"] == expected_breaks
    assert result["resume_dates"] == expected_resumes


def test_struggled_habits_sorting_and_scoring(db_session: SQLAlchemySession):
    """Test the main struggled_habits function for correct scoring and sorting."""
    now = datetime.now()
    
    # Habit A: Perfect streak -> Score 0
    habit_a = _add_habit(db_session, "Perfect Habit", "daily")
    habit_a.completions.extend([
        Completion(completion_date=now - timedelta(days=1)),
        Completion(completion_date=now),
    ])
    
    # Habit B: One small break -> Score 2 (1 break + 1 gap day)
    habit_b = _add_habit(db_session, "Okay Habit", "daily")
    habit_b.completions.extend([
        Completion(completion_date=now - timedelta(days=3)),
        Completion(completion_date=now - timedelta(days=1)),
    ])
    
    # Habit C: Most struggled -> Score 6 (1 break + 5 gap days)
    habit_c = _add_habit(db_session, "Struggled Habit", "daily")
    habit_c.completions.extend([
        Completion(completion_date=now - timedelta(days=10)),
        Completion(completion_date=now - timedelta(days=4)),
    ])
    db_session.commit()
    
    results = struggled_habits(db_session)
    
    # Check that we have results for all 3 habits
    assert len(results) == 3
    
    # Check the sorting order (most struggled first)
    assert results[0]["habit"].name == "Struggled Habit"
    assert results[1]["habit"].name == "Okay Habit"
    assert results[2]["habit"].name == "Perfect Habit"
    
    # Check the scores
    assert results[0]["score"] == 6 # 1 break + (10-4-1)=5 gap days
    assert results[1]["score"] == 2 # 1 break + (3-1-1)=1 gap day
    assert results[2]["score"] == 0 # 0 breaks + 0 gap days


def test_generate_summary_no_habits(db_session: SQLAlchemySession):
    """Test that the summary handles an empty database correctly."""
    summary = generate_summary(db_session)
    assert summary == "No habits registered."


def test_generate_summary_with_data(db_session: SQLAlchemySession):
    """Test the full summary generation with a variety of habit data."""
    now = datetime.now()

    # --- Setup a controlled set of habits ---
    # 1. Daily Habits (1 completed, 1 not)
    daily_done = _add_habit(db_session, "Daily Done", "daily")
    daily_done.completions.append(Completion(completion_date=now))
    _add_habit(db_session, "Daily Not Done", "daily")

    # 2. Weekly Habits (1 completed, 1 not)
    weekly_done = _add_habit(db_session, "Weekly Done", "weekly")
    weekly_done.completions.append(Completion(completion_date=now))
    weekly_not_done = _add_habit(db_session, "Weekly Not Done", "weekly")
    weekly_not_done.completions.append(
        Completion(completion_date=now - timedelta(days=10)) # Last week
    )

    # 3. Monthly Habits (1 completed, 1 not)
    monthly_done = _add_habit(db_session, "Monthly Done", "monthly")
    monthly_done.completions.append(Completion(completion_date=now))
    _add_habit(db_session, "Monthly Not Done", "monthly")

    # 4. Performance Habits
    # Most struggled: 1 break, 4 gap days -> struggle score 5
    struggled = _add_habit(db_session, "Struggled Habit", "daily")
    struggled.completions.extend([
        Completion(completion_date=now - timedelta(days=10)),
        Completion(completion_date=now - timedelta(days=5)),
    ])
    # Best performing: perfect streak -> struggle score 0
    perfect = _add_habit(db_session, "Perfect Habit", "daily")
    perfect.completions.extend([
        Completion(completion_date=now - timedelta(days=1)),
        Completion(completion_date=now),
    ])
    
    db_session.commit()

    # --- Generate and Assert ---
    summary = generate_summary(db_session)

    # Check for key phrases and values in the output string
    assert "Total Registered Habits: 8" in summary
    assert "Daily (Completed / Total):   2 / 4" in summary # 3 daily habits total
    assert "Weekly (Completed / Total):  1 / 2" in summary
    assert "Monthly (Completed / Total): 1 / 2" in summary
    assert "Best Performing Habit: Perfect Habit" in summary
    assert "Most Struggled Habit:  Struggled Habit" in summary
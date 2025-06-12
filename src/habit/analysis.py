import calendar
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from .habit_manager import PERIODICITIES, HabitManager
from .models import Habit


def _is_completed_in_current_period(habit: Habit, current_time: datetime) -> bool:
    """Checks if a habit was completed in its current period.

    A single, consistent function to check if a habit was completed today
    (for daily), this week (for weekly), or this month (for monthly).

    Args:
        habit (Habit): The habit object to check.
        current_time (datetime): The reference time, typically datetime.now().

    Returns:
        bool: True if the habit was completed within its current period,
                False otherwise.
    """
    today = current_time.date()
    if habit.periodicity == "daily":
        return any(c.completion_date.date() == today for c in habit.completions)
    elif habit.periodicity == "weekly":
        start_of_week = today - timedelta(days=today.weekday())
        return any(
            c.completion_date.date() >= start_of_week for c in habit.completions
        )
    elif habit.periodicity == "monthly":
        start_of_month = today.replace(day=1)
        return any(
            c.completion_date.date() >= start_of_month for c in habit.completions
        )
    return False


def _calculate_current_deadline(habit: Habit, current_time: datetime) -> datetime:
    """Calculates the upcoming deadline for a habit based on its periodicity.

    - Daily: End of the current day.
    - Weekly: End of the current week (Sunday).
    - Monthly: End of the current month.

    Args:
        habit (Habit): The habit object.
        current_time (datetime): The reference time, typically datetime.now().

    Returns:
        datetime: The calculated deadline for the habit's current period.
    """
    if habit.periodicity == "daily":
        return current_time.replace(hour=23, minute=59, second=59, microsecond=0)
    elif habit.periodicity == "weekly":
        days_until_sunday = 6 - current_time.weekday()
        deadline_date = current_time + timedelta(days=days_until_sunday)
        return deadline_date.replace(
            hour=23, minute=59, second=59, microsecond=0
        )
    elif habit.periodicity == "monthly":
        _, last_day = calendar.monthrange(current_time.year, current_time.month)
        return current_time.replace(
            day=last_day, hour=23, minute=59, second=59, microsecond=0
        )
    return current_time


def _periodicity(session: Session, periodicity: str) -> List[Habit]:
    """Filters habits by a specific periodicity.

    Args:
        session (Session): The database session.
        periodicity (str): The period to filter by (e.g., 'daily', 'weekly').

    Returns:
        List[Habit]: A list of matching Habit objects.
    """
    if periodicity not in PERIODICITIES:
        return []
    return session.query(Habit).filter(Habit.periodicity == periodicity).all()


def _get_habits_for_generation(
    session: Session,
    periodicity: Optional[str] = None,
    habits: Optional[List[Habit]] = None,
) -> List[Habit]:
    """Internal helper to resolve the list of habits to be processed.

    If a list of habits is provided, it is returned directly. Otherwise,
    it queries the database based on the optional periodicity filter.

    Args:
        session (Session): The database session.
        periodicity (Optional[str]): An optional periodicity to filter by.
        habits (Optional[List[Habit]]): An optional pre-supplied list of habits.

    Returns:
        List[Habit]: The definitive list of habits to be processed.
    """
    if habits is not None:
        return habits
    if periodicity:
        return _periodicity(session, periodicity)
    return session.query(Habit).all()


def generate_table(
    session: Session,
    periodicity: Optional[str] = None,
    habits: Optional[List[Habit]] = None,
) -> str:
    """Generates a formatted string table of habits.

    Can be filtered by periodicity or a pre-supplied list of habits.

    Args:
        session (Session): The database session.
        periodicity (Optional[str]): An optional periodicity to filter by.
        habits (Optional[List[Habit]]): An optional pre-supplied list of habits.

    Returns:
        str: A multi-line string representing the formatted table.
    """
    habits_to_process = _get_habits_for_generation(session, periodicity, habits)
    current_time = datetime.now()
    header = ["Status", "Name", "Description", "Created", "Deadline"]
    rows = [header]

    for habit in habits_to_process:
        is_checked = _is_completed_in_current_period(habit, current_time)
        status = "☑" if is_checked else "☐"
        name_trunc = (
            (habit.name[:18] + "..") if len(habit.name) > 20 else habit.name
        )
        desc_trunc = (
            (habit.description[:22] + "..")
            if habit.description and len(habit.description) > 25
            else (habit.description or "")
        )
        deadline = _calculate_current_deadline(habit, current_time)
        rows.append(
            [
                status,
                name_trunc,
                desc_trunc,
                habit.creation_date.strftime("%Y-%m-%d"),
                deadline.strftime("%Y-%m-%d"),
            ]
        )

    widths = [max(len(str(item)) for item in col) for col in zip(*rows)]
    header_line = " | ".join(f"{h:<{w}}" for h, w in zip(rows[0], widths))
    separator = "-+-".join("-" * w for w in widths)
    data_lines = [
        " | ".join(f"{item:<{w}}" for item, w in zip(row, widths))
        for row in rows[1:]
    ]
    return "\n".join([header_line, separator] + data_lines)


def generate_list(
    session: Session,
    periodicity: Optional[str] = None,
    habits: Optional[List[Habit]] = None,
) -> List[str]:
    """Generates a list of formatted strings for habits.

    Can be filtered by periodicity or a pre-supplied list of habits.

    Args:
        session (Session): The database session.
        periodicity (Optional[str]): An optional periodicity to filter by.
        habits (Optional[List[Habit]]): An optional pre-supplied list of habits.

    Returns:
        List[str]: A list of human-readable strings, one for each habit.
    """
    habits_to_process = _get_habits_for_generation(session, periodicity, habits)
    current_time = datetime.now()
    output_list = []

    for habit in habits_to_process:
        is_checked = _is_completed_in_current_period(habit, current_time)
        status = "☑" if is_checked else "☐"
        desc = habit.description or ""
        deadline = _calculate_current_deadline(habit, current_time)
        deadline_str = deadline.strftime("%Y-%m-%d %H:%M")
        output_list.append(
            f"{status} {habit.name}: {desc} The deadline is {deadline_str}."
        )
    return output_list


def _get_sorted_unique_dates(habit: Habit) -> List[date]:
    """Internal helper to get a sorted list of unique completion dates.

    Args:
        habit (Habit): The habit to analyze.

    Returns:
        List[date]: A sorted list of unique dates of completion.
    """
    if not habit.completions:
        return []
    return sorted(list({comp.completion_date.date() for comp in habit.completions}))


def _calculate_streak_for_dates(dates: List[datetime]) -> int:
    """Helper to calculate the longest consecutive day streak from datetimes.

    Args:
        dates (List[datetime]): A list of completion datetimes.

    Returns:
        int: The length of the longest consecutive day streak.
    """
    if not dates:
        return 0
    unique_dates = sorted(list({d.date() for d in dates}))
    if not unique_dates:
        return 0

    longest = 1
    current = 1
    for i in range(1, len(unique_dates)):
        if unique_dates[i] - unique_dates[i - 1] == timedelta(days=1):
            current += 1
        else:
            current = 1
        if current > longest:
            longest = current
    return longest


def longest_streak(session: Session, identifier: Optional[int | str] = None) -> int:
    """Finds the longest streak from all habits or for a specific habit.

    Args:
        session (Session): The database session.
        identifier (Optional[int | str]): The ID or name of a specific habit.
            If None, checks all habits to find the overall longest streak.

    Returns:
        int: The highest number of consecutive days a habit was completed.
    """
    manager = HabitManager(session)
    habits_to_check: List[Habit] = []

    if identifier is not None:
        habit = manager.find_habit(identifier)
        if habit:
            habits_to_check.append(habit)
    else:
        habits_to_check = manager.get_all_habits()

    if not habits_to_check:
        return 0

    overall_max_streak = 0
    for habit in habits_to_check:
        completion_dates = [comp.completion_date for comp in habit.completions]
        streak = _calculate_streak_for_dates(completion_dates)
        if streak > overall_max_streak:
            overall_max_streak = streak
    return overall_max_streak


def _break_count(habit: Habit) -> int:
    """Calculates the number of times a habit's streak was broken.

    Args:
        habit (Habit): The habit to analyze.

    Returns:
        int: The total number of times a streak was broken.
    """
    unique_dates = _get_sorted_unique_dates(habit)
    if len(unique_dates) <= 1:
        return 0
    breaks = 0
    for i in range(1, len(unique_dates)):
        if (unique_dates[i] - unique_dates[i - 1]) > timedelta(days=1):
            breaks += 1
    return breaks


def _gap_count(habit: Habit) -> int:
    """Calculates the total number of missed days between streaks.

    Args:
        habit (Habit): The habit to analyze.

    Returns:
        int: The sum of all gap days between broken streaks.
    """
    unique_dates = _get_sorted_unique_dates(habit)
    if len(unique_dates) <= 1:
        return 0
    total_gap_days = 0
    for i in range(1, len(unique_dates)):
        diff = unique_dates[i] - unique_dates[i - 1]
        if diff.days > 1:
            total_gap_days += diff.days - 1
    return total_gap_days


def _gap_days(habit: Habit) -> Dict[str, List[date]]:
    """Identifies the dates when streaks were broken and when they resumed.

    Args:
        habit (Habit): The habit to analyze.

    Returns:
        Dict[str, List[date]]: A dictionary with 'break_dates' (last day of a
            streak) and 'resume_dates' (first day of the next).
    """
    unique_dates = _get_sorted_unique_dates(habit)
    result = {"break_dates": [], "resume_dates": []}
    if len(unique_dates) <= 1:
        return result
    for i in range(1, len(unique_dates)):
        if (unique_dates[i] - unique_dates[i - 1]) > timedelta(days=1):
            result["break_dates"].append(unique_dates[i - 1])
            result["resume_dates"].append(unique_dates[i])
    return result


def struggled_habits(session: Session) -> List[Dict[str, Any]]:
    """Analyzes all habits to find the most "struggled" ones.

    Calculates a struggle score for each habit where:
    Struggle Score = (Number of Breaks) + (Total Gap Days).

    Args:
        session (Session): The database session.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, one for each habit,
            sorted by the struggle score in descending order. Each dictionary
            contains the habit object, score, breaks, and gaps.
    """
    manager = HabitManager(session)
    all_habits = manager.get_all_habits()
    habit_scores = []
    for habit in all_habits:
        breaks = _break_count(habit)
        gaps = _gap_count(habit)
        score = breaks + gaps
        habit_scores.append(
            {"habit": habit, "score": score, "breaks": breaks, "gaps": gaps}
        )
    return sorted(habit_scores, key=lambda x: x["score"], reverse=True)


def generate_summary(session: Session) -> str:
    """Generates a high-level string summary of the overall habit landscape.

    Args:
        session (Session): The database session.

    Returns:
        str: A formatted, multi-line string with the summary statistics.
    """
    manager = HabitManager(session)
    all_habits = manager.get_all_habits()
    if not all_habits:
        return "No habits registered."

    now = datetime.now()
    daily_completed = sum(
        1
        for h in all_habits
        if h.periodicity == "daily" and _is_completed_in_current_period(h, now)
    )
    weekly_completed = sum(
        1
        for h in all_habits
        if h.periodicity == "weekly" and _is_completed_in_current_period(h, now)
    )
    monthly_completed = sum(
        1
        for h in all_habits
        if h.periodicity == "monthly" and _is_completed_in_current_period(h, now)
    )
    daily_total = sum(1 for h in all_habits if h.periodicity == "daily")
    weekly_total = sum(1 for h in all_habits if h.periodicity == "weekly")
    monthly_total = sum(1 for h in all_habits if h.periodicity == "monthly")

    struggle_results = struggled_habits(session)
    most_struggled = struggle_results[0]["habit"].name if struggle_results else "N/A"
    best_performing = struggle_results[-1]["habit"].name if struggle_results else "N/A"

    summary = f"""
--- Habit Summary ---
Total Registered Habits: {len(all_habits)}

Periodicity Breakdown:
- Daily (Completed / Total):   {daily_completed} / {daily_total}
- Weekly (Completed / Total):  {weekly_completed} / {weekly_total}
- Monthly (Completed / Total): {monthly_completed} / {monthly_total}

Performance Highlights:
- Best Performing Habit: {best_performing}
- Most Struggled Habit:  {most_struggled}
---------------------
"""
    return summary.strip()
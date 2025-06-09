
"""
must be implemented using the functional programming paradigm. 
return a list of all currently tracked habits,
return a list of all habits with the same periodicity,
return the longest run streak of all defined habits,
return the longest run streak for a given habit.
what’s my longest habit streak? 
What's the list of my current daily habits? 
With which habits did I struggle most last month? and so on
"""

"""

    func 1: return a list of all currently tracked habits 
    
    func 2: return a list of all habits with the same periodicity
    
    func 3: return the longest streak of a given habit.
    
    func 4: list of habits today. habits that I have to do today.
    
    func 5: return the longest streak of all defined habits.
    
    func 6: with which habit did I struggle with the most? 
    we can specify time range or this week/this month/this year
    this is based on how long i paused and how many times i paused it by calculating 
    Struggle score = number_of_gaps + total_gap_days.
    utility func 1: calculate gaps length
    utility func 2: calculate number of gaps
    
    Returns a list of dictionaries with habit info and score.
    
    func 7: provide a comprehensive summary string that can be printed on terminal

"""

# def _calculate_current_deadline(habit: Habit, current_time: datetime) -> datetime:
#     """
#     Calculates the upcoming deadline for a habit based on its periodicity
#     and the current time.
#     - Daily: End of the current day.
#     - Weekly: End of the current week (Sunday).
#     - Monthly: End of the current month.
#     """

# def _periodicity():
#     """
#     utility function that filter result by daily, weekly, monthly
#     returns a list of habits
#     """

# def generate_table():
#     """
#     all habits by default 
#     optionally you can pass periodicity (daily, weekly, monthly) using _periodicity()
#     optionally you can pass a list of habit
    
#     the table will have 
#     status | name (truncated )| truncated (truncated) | creation date | deadline
#     returns a string that contains a table or list of selected habits
    
#     deadline will be calculated with _calculate_deadline()
#     """

# def generate_list(): 
#     """
#     all habits by default 
#     optionally you can pass periodicity (daily, weekly, monthly) using _periodicity()
#     optionally you can pass a list of habit
    
#     the list will follow this format
#     ☑/☐ habit name :  description. the deadline is (date and time of the deadline).
#     """


    
# def longest_streak():
#     """
#     find a return the longest streak from all habits 
#     or the the longest streak for a given habit.
#     optionally we can pass habits name or id
#     """

# def _break_count():
#     """
#     it takes habit as a param and check the number of breaks in a habit.
#     then return a count
#     """
    
# def _gap_count():
#     """
#     use the _number_of_breaks() to get when the habits stopped.
#     then calculate how many days till the user checkoff habit again.
#     the difference between when habits stopped and when checkoff happened again
#     is the number of gap.
    
#     return a count of total gap days for between breaks and checkoffs, 
    
#     """ 

# def _gap_days():
#     """
#     return a list days when these habits were broken
#     and a list of dates when the streak was resumed
#     """

# def struggled_habits():
#     """
#     Here we will introduce a habit score to compare between habits.
#     the score is caculated as Struggle score = _break_count() + _gap_count().
#     """


from datetime import date, datetime, timedelta
import calendar
from typing import Dict, List, Optional, Any


from sqlalchemy.orm import Session

from models import Habit, Completion
from habit_manager import HabitManager, PERIODICITIES


def _calculate_current_deadline(habit: Habit, current_time: datetime) -> datetime:
    """
    Calculates the upcoming deadline for a habit based on its periodicity
    and the current time.
    - Daily: End of the current day.
    - Weekly: End of the current week (Sunday).
    - Monthly: End of the current month.
    """
    if habit.periodicity == "daily":
        # End of the current day
        return current_time.replace(hour=23, minute=59, second=59, microsecond=0)

    elif habit.periodicity == "weekly":
        # Days until Sunday (where Monday is 0 and Sunday is 6)
        days_until_sunday = 6 - current_time.weekday()
        deadline_date = current_time + timedelta(days=days_until_sunday)
        return deadline_date.replace(
            hour=23, minute=59, second=59, microsecond=0
        )

    elif habit.periodicity == "monthly":
        # Last day of the current month
        _, last_day = calendar.monthrange(current_time.year, current_time.month)
        return current_time.replace(
            day=last_day, hour=23, minute=59, second=59, microsecond=0
        )

    # Fallback for unknown periodicity, though manager validation should prevent this
    return current_time


def _periodicity(session: Session, periodicity: str) -> List[Habit]:
    """
    Utility function that filters habits by daily, weekly, or monthly.
    Returns a list of matching Habit objects.
    """
    if periodicity not in PERIODICITIES:
        # Or raise ValueError, depending on desired strictness
        return []
    return session.query(Habit).filter(Habit.periodicity == periodicity).all()


def _get_habits_for_generation(
    session: Session,
    periodicity: Optional[str] = None,
    habits: Optional[List[Habit]] = None,
) -> List[Habit]:
    """Helper to resolve the list of habits to be used in generation."""
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
    """
    Generates a formatted string table of habits.
    Can be filtered by periodicity or a pre-supplied list of habits.
    """
    habits_to_process = _get_habits_for_generation(session, periodicity, habits)
    current_time = datetime.now()

    header = ["Status", "Name", "Description", "Created", "Deadline"]
    rows = [header]

    for habit in habits_to_process:
        # Check if there's a completion within the current period
        deadline = _calculate_current_deadline(habit, current_time)
        # Approximation for check daily 1, weekly 7, or monthly 30
        start_of_period = deadline - timedelta(days=1 if habit.periodicity == "daily" else 7 if habit.periodicity == "weekly" else 30)
        
        is_checked = any(
            comp.completion_date > start_of_period for comp in habit.completions
        )
        status = "☑" if is_checked else "☐"

        name_trunc = (
            (habit.name[:18] + "..") if len(habit.name) > 20 else habit.name
        )
        desc_trunc = (
            (habit.description[:22] + "..")
            if habit.description and len(habit.description) > 25
            else (habit.description or "")
        )

        rows.append([
            status,
            name_trunc,
            desc_trunc,
            habit.creation_date.strftime("%Y-%m-%d"),
            deadline.strftime("%Y-%m-%d"),
        ])

    # Calculate column widths for alignment
    widths = [max(len(str(item)) for item in col) for col in zip(*rows)]
    # Format the table, long strings will be truncated.
    header_line = " | ".join(
        f"{h:<{w}}" for h, w in zip(rows[0], widths)
    )
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
    """
    Generates a list of formatted strings for habits.
    Can be filtered by periodicity or a pre-supplied list of habits.
    """
    habits_to_process = _get_habits_for_generation(session, periodicity, habits)
    current_time = datetime.now()
    output_list = []

    for habit in habits_to_process:
        deadline = _calculate_current_deadline(habit, current_time)
        start_of_period = deadline - timedelta(days=1 if habit.periodicity == "daily" else 7 if habit.periodicity == "weekly" else 30) # Approximation for check
        
        is_checked = any(
            comp.completion_date > start_of_period for comp in habit.completions
        )
        status = "☑" if is_checked else "☐"
        
        desc = habit.description or ""
        deadline_str = deadline.strftime("%Y-%m-%d %H:%M")
        
        output_list.append(
            f"{status} {habit.name}: {desc} The deadline is {deadline_str}."
        )
        
    return output_list

def _calculate_streak_for_dates(dates: List[datetime]) -> int:
    """
    Helper function to calculate the longest consecutive day streak from a list of datetimes.
    """
    if not dates:
        return 0

    # Get unique dates (ignoring time) and sort them
    unique_dates = sorted(list({d.date() for d in dates}))

    if not unique_dates:
        return 0

    longest = 1
    current = 1
    for i in range(1, len(unique_dates)):
        # Check if the current date is exactly one day after the previous one
        if unique_dates[i] - unique_dates[i - 1] == timedelta(days=1):
            current += 1
        else:
            # Streak is broken, reset current streak
            current = 1
        
        if current > longest:
            longest = current
            
    return longest


def longest_streak(session: Session, identifier: Optional[int | str] = None) -> int:
    """
    Finds and returns the longest streak from all habits or for a given habit.

    Args:
        session (Session): The database session.
        identifier (int | str, optional): The ID or name of a specific habit.
                                          If None, checks all habits.

    Returns:
        int: The highest number of consecutive days a habit was completed.
             Returns 0 if there are no completions.
    """
    manager = HabitManager(session)
    habits_to_check: List[Habit] = []

    if identifier is not None:
        habit = manager.find_habit(identifier)
        if habit:
            habits_to_check.append(habit)
    else:
        # If no identifier, get all habits
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

def _get_sorted_unique_dates(habit: Habit) -> List[date]:
    """
    Internal helper to get a sorted list of unique completion dates for a habit.
    """
    if not habit.completions:
        return []
    # Use a set to get unique dates (ignoring time), then sort the list
    return sorted(list({comp.completion_date.date() for comp in habit.completions}))


def _break_count(habit: Habit) -> int:
    """
    Checks the number of breaks in a habit's completion history.
    A break is any time the streak of consecutive days is broken.

    Returns:
        int: The total number of times a streak was broken.
    """
    unique_dates = _get_sorted_unique_dates(habit)
    if len(unique_dates) <= 1:
        return 0

    breaks = 0
    for i in range(1, len(unique_dates)):
        # If the gap is more than one day, a break occurred.
        if (unique_dates[i] - unique_dates[i - 1]) > timedelta(days=1):
            breaks += 1
    return breaks


def _gap_count(habit: Habit) -> int:
    """
    Calculates the total number of missed days between streaks.

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
            # The gap is the number of days between - 1
            # e.g., gap between Mon and Wed is 1 day (Tue)
            total_gap_days += diff.days - 1
    return total_gap_days


def _gap_days(habit: Habit) -> Dict[str, List[date]]:
    """
    Identifies the specific dates when streaks were broken and when they resumed.

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
    """
    Analyzes all habits to find the most "struggled" ones based on a score.
    Struggle Score = (Number of Breaks) + (Total Gap Days).

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, one for each habit,
                              sorted by the struggle score in descending order.
    """
    manager = HabitManager(session)
    all_habits = manager.get_all_habits()
    
    habit_scores = []
    for habit in all_habits:
        breaks = _break_count(habit)
        gaps = _gap_count(habit)
        score = breaks + gaps
        
        habit_scores.append({
            "habit": habit,
            "score": score,
            "breaks": breaks,
            "gaps": gaps,
        })
        
    # Sort by score, descending
    return sorted(habit_scores, key=lambda x: x["score"], reverse=True)

def generate_summary(session: Session) -> str:
    """
    Generates a string summary of the overall habit landscape.

    Includes counts of total, completed, and uncompleted habits by
    periodicity, and identifies the best and most struggled-with habits.

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
    today = now.date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    # Initialize counters
    daily_completed, daily_total = 0, 0
    weekly_completed, weekly_total = 0, 0
    monthly_completed, monthly_total = 0, 0

    for habit in all_habits:
        if habit.periodicity == "daily":
            daily_total += 1
            if any(c.completion_date.date() == today for c in habit.completions):
                daily_completed += 1
        elif habit.periodicity == "weekly":
            weekly_total += 1
            if any(c.completion_date.date() >= start_of_week for c in habit.completions):
                weekly_completed += 1
        elif habit.periodicity == "monthly":
            monthly_total += 1
            if any(c.completion_date.date() >= start_of_month for c in habit.completions):
                monthly_completed += 1

    # Get struggle analysis
    struggle_results = struggled_habits(session)
    most_struggled = struggle_results[0]["habit"].name if struggle_results else "N/A"
    best_performing = struggle_results[-1]["habit"].name if struggle_results else "N/A"

    # Build the output string
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

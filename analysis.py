
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

# def _date_range():
#     """
#     utility function that filters result by start_date and/or end_date
#     in which start_date is from a date until now by default
#     and end_date is from the beginning of all habits until specified date.
#     returns a list of habits
#     """

# def _periodicity():
#     """
#     utility function that filter result by daily, weekly, monthly
#     returns a list of habits
#     """


# def print_habits():
#     """
#     print all habits by default 
#     optionally you can pass periodicity (daily, weekly, monthly) uding _periodicity()
#     optionally you can also pass range starting date and ending date using _date_range()
#     optionally you can pass a list of habit
    
#     the list will follow this format
#     ☑/☐ habit name :  description. the deadline is (date and time of the deadline).
    
#     the table will have 
#     status | name (truncated )| truncated (truncated) | creation date | deadline
#     returns a string that contains a table or list of selected habits
    
#     """ 

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from models import Habit

def _date_range(
    session: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    habits: Optional[List[Habit]] = None,
) -> List[Habit]:
    """
    Filters habits by creation_date between start_date and end_date.
    If habits is provided, filters that list instead of querying all.
    """
    if habits is None:
        habits = session.query(Habit).all()
    filtered = []
    for habit in habits:
        cdate = habit.creation_date.date()
        if start_date and cdate < start_date:
            continue
        if end_date and cdate > end_date:
            continue
        filtered.append(habit)
    return filtered

def _periodicity(
    session: Session,
    periodicity: Optional[str] = None,
    habits: Optional[List[Habit]] = None,
) -> List[Habit]:
    """
    Filters habits by periodicity (daily, weekly, monthly).
    If habits is provided, filters that list instead of querying all.
    """
    if periodicity is None:
        return habits if habits is not None else session.query(Habit).all()
    periodicity = periodicity.lower()
    if habits is None:
        habits = session.query(Habit).all()
    return [h for h in habits if getattr(h, "periodicity", "daily").lower() == periodicity]

def print_habits(
    session: Session,
    periodicity: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    habits: Optional[List[Habit]] = None,
) -> str:
    """
    Print all habits, optionally filtered by periodicity and/or date range.
    Returns a string containing a dict with a 'table' key and a 'list' key.
    """
    # Compose filters
    selected = habits if habits is not None else session.query(Habit).all()
    if periodicity:
        selected = _periodicity(session, periodicity, selected)
    if start_date or end_date:
        selected = _date_range(session, start_date, end_date, selected)

    # Prepare table
    def truncate(s, n):
        return (s[: n - 3] + "...") if s and len(s) > n else (s or "")

    table_rows = []
    list_rows = []
    for habit in selected:
        # Status: checked if last completion is today, unchecked otherwise
        completions = getattr(habit, "completions", [])
        today = datetime.now().date()
        status = "☑" if any(
            c.completion_date.date() == today for c in completions
        ) else "☐"
        name = truncate(habit.name, 16)
        desc = truncate(habit.description, 20)
        cdate = habit.creation_date.strftime("%Y-%m-%d")
        # For deadline, let's assume daily: today+1, weekly: next week, monthly: next month
        periodicity_val = getattr(habit, "periodicity", "daily").lower()
        if periodicity_val == "daily":
            deadline = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif periodicity_val == "weekly":
            deadline = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        elif periodicity_val == "monthly":
            deadline = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        else:
            deadline = "N/A"
        table_rows.append([status, name, desc, cdate, deadline])
        list_rows.append(
            f"{status} {habit.name} : {habit.description}. the deadline is ({deadline})."
        )

    # Format table as a string
    header = ["status", "name", "description", "creation date", "deadline"]
    table_str = (
        " | ".join(header)
        + "\n"
        + "-" * 60
        + "\n"
        + "\n".join(
            " | ".join(row) for row in table_rows
        )
    )

    result = {
        "table": table_str,
        "list": list_rows,
    }
    return str(result)
    
def longest_streak():
    """
    return the longest streak in a habit and which habit it belongs to 
    or the the longest streak for a given habit.
    optionally you can pass range by _date_range()
    optionally we can pass habits name or id through HabitManager class
    """

def _break_count():
    """
    it takes habit as a param and check the number of breaks in a habit.
    then return a count
    """
    
def _gap_count():
    """
    use the _number_of_breaks() to get when the habits stopped.
    then calculate how many days till the user checkoff habit again.
    the difference between when habits stopped and when checkoff happened again
    is the number of gap.
    
    return a count of total gap days for between breaks and checkoffs, 
    
    """ 

def _gap_days():
    """
    return a list days when these habits were broken
    and a list of dates when the streak was resumed
    """

def struggled_habits():
    """
    Here we will introduce a habit score to compare between habits.
    the score is caculated as Struggle score = _break_count() + _gap_count().
    """

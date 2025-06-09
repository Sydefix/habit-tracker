# fixtures.py

from datetime import datetime, timedelta

def get_fixtures():
    """
    Generates a list of dictionaries representing habits and their completions.
    Daily habits are relative to the current day for relevance.
    Weekly and Monthly habits use fixed calendar dates for deterministic history.
    """
    # Making this fixture I realized a lot of things.
    # first, if we use timedelta, everyone will get different dates from different times.
    # For example, today is 7th day of the week and tomorrow starts a new week.
    # There is no way for deltatime() to know if we started a new week or not.
    # some people will get extra week streaks and others will not get any.
    
    # writing hardcoded timestamps will not be consistent either. 
    
    # preferrably our habits should align with calendar dynamically because
    # our work and life arrangements also aligns with calendar dates like our usual off days.
    
    # so in order to keep consistent result by making it dynamic,
    # I created the function as follow:
    
    # --- Date Setup ---
    now = datetime.now()
    current_year = now.year

    # Helper to get dates from previous months, handling year change from January
    def get_past_month(months_ago):
        month = now.month - months_ago
        year = current_year
        while month <= 0:
            month += 12
            year -= 1
        return year, month

    last_month_year, last_month = get_past_month(1)
    two_months_ago_year, two_months_ago_month = get_past_month(2)

    # --- Fixture Data ---
    fixtures = [
        # --- DAILY HABITS (relative to 'now') ---
        {
            "habit": {
                "name": "Daily Meditation",
                "description": "10 minutes of mindfulness.",
                "periodicity": "daily",
            },
            "completions": [
                now - timedelta(days=2), now - timedelta(days=1), now,
            ],
        },
        {
            "habit": {
                "name": "Workout",
                "description": "At least 30 minutes of exercise.",
                "periodicity": "daily",
            },
            "completions": [
                now - timedelta(days=40), now - timedelta(days=20),
            ],
        },
        {
            "habit": {
                "name": "Read a Book",
                "description": "Read at least one chapter.",
                "periodicity": "daily",
            },
            "completions": [(now - timedelta(days=2)).replace(hour=9)],
        },
        {
            "habit": {
                "name": "Practice Guitar",
                "description": "A new habit with no completions yet.",
                "periodicity": "daily",
            },
            "completions": [],
        },
        {
            "habit": {
                "name": "Morning Journal",
                "description": "Write one page of thoughts.",
                "periodicity": "daily",
            },
            "completions": [now - timedelta(days=d) for d in range(10)],
        },
        {
            "habit": {
                "name": "Code for 30 Minutes",
                "description": "Work on a personal project.",
                "periodicity": "daily",
            },
            "completions": [now - timedelta(days=d) for d in range(1, 15, 2)],
        },
        {
            "habit": {
                "name": "Learn Spanish on Duolingo",
                "description": "Complete one lesson.",
                "periodicity": "daily",
            },
            "completions": [now - timedelta(days=55)],
        },
        {
            "habit": {
                "name": "Tidy Desk",
                "description": None,
                "periodicity": "daily",
            },
            "completions": [now],
        },
        # --- WEEKLY HABITS (fixed calendar dates) ---
        {
            "habit": {
                "name": "Weekly Review",
                "description": "Plan the upcoming week.",
                "periodicity": "weekly",
            },
            "completions": [
                datetime(two_months_ago_year, two_months_ago_month, 10),
                datetime(last_month_year, last_month, 15),
                now,  # Completed this week to show as '☑'
            ],
        },
        {
            "habit": {
                "name": "Submit Timesheet",
                "description": "Submit hours for payroll.",
                "periodicity": "weekly",
            },
            "completions": [
                datetime(last_month_year, last_month, 22),
                now,  # Completed this week
            ],
        },
        {
            "habit": {
                "name": "Water the Plants",
                "description": "Check soil and water if needed.",
                "periodicity": "weekly",
            },
            "completions": [
                datetime(last_month_year, last_month, 1),
                now,  # Completed this week
            ],
        },
        {
            "habit": {
                "name": "Organize Digital Files",
                "description": "Clean up desktop and downloads folder.",
                "periodicity": "weekly",
            },
            "completions": [datetime(last_month_year, last_month, 5)],
        },
        {
            "habit": {
                "name": "Call Family or Friends",
                "description": "Catch up with a loved one.",
                "periodicity": "weekly",
            },
            "completions": [
                datetime(two_months_ago_year, two_months_ago_month, 1),
                datetime(last_month_year, last_month, 1),
            ],
        },
        # --- MONTHLY HABITS (fixed calendar dates) ---
        {
            "habit": {
                "name": "Pay Monthly Bills",
                "description": "Pay rent, utilities, etc.",
                "periodicity": "monthly",
            },
            "completions": [
                datetime(two_months_ago_year, two_months_ago_month, 28)
            ],
        },
        {
            "habit": {
                "name": "Review Monthly Budget",
                "description": "Check spending against budget.",
                "periodicity": "monthly",
            },
            "completions": [
                datetime(last_month_year, last_month, 25),
                now,  # Completed this month
            ],
        },
    ]
    return fixtures
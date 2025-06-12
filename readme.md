# Habit Tracker CLI

A command-line application for building, tracking, and analyzing your habits directly from the terminal. Built with Python, SQLAlchemy, and Click.

![Python Version](https://img.shields.io/badge/python-3.8+-brightgreen.svg)

This application provides a robust set of tools for personal development, featuring a full management suite, a powerful analysis engine, and a safe, sandboxed demo environment to explore all its capabilities.

## Key Features

-   **Full Habit Management:** Add, update, delete, and checkoff habits with simple commands.
-   **Flexible Periodicity:** Track habits that are daily, weekly, or monthly.
-   **Powerful Analysis Engine:** Gain insights with detailed analytics for streaks, struggle scores, and progress summaries.
-   **Safe Demo Environment:** A sandboxed "playground" with a separate database and rich fixture data.
-   **Intuitive CLI:** A user-friendly command-line interface powered by `click`.

## Demo in Action

Here’s a quick look at what you can do with the Habit Tracker CLI, using the built-in demo environment.

- First, start the demo environment to create and seed the demo database
```bash
$ habit demo start
Creating new demo database...
Loading fixtures...
Fixtures loaded successfully.
```
- Get a high-level summary of the demo data
```bash
$ habit demo analyze --show summary
--- Habit Summary ---
Total Registered Habits: 15

Periodicity Breakdown:
- Daily (Completed / Total):   3 / 8
- Weekly (Completed / Total):  3 / 5
- Monthly (Completed / Total): 1 / 2

Performance Highlights:
- Best Performing Habit: Pay Monthly Bills
- Most Struggled Habit:  Weekly Review
---------------------
```
- Checkoff a habit in the demo
```bash
$ habit demo checkoff "Workout"
Successfully checked off habit: 'Workout'. Keep it up!
```
- See the struggle scores for all habits
```bash
$ habit demo analyze --show struggle
--- Habit Struggle Score (Higher is worse) ---
  - Weekly Review: Score 63 (2 breaks, 61 gap days)
  - Water the Plants: Score 42 (1 breaks, 41 gap days)
  - Call Family or Friends: Score 30 (1 breaks, 29 gap days)
  - Submit Timesheet: Score 21 (1 breaks, 20 gap days)
  # ... and so on
```

## Quick Start

Get up and running in just a few steps.

**1. Clone the Repository**
```bash
git clone https://github.com/Sydefix/habit-tracker.git
cd habit-tracker
```

**2. Set Up a Virtual Environment (Recommended)**
```bash
# On macOS / Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
.\venv\Scripts\activate
```

**3. Install Dependencies**
```bash
pip install -e ".[dev]"
```

**4. Run the Application**
```bash
habit --help
```

For more detailed instructions, please see the **[Installation and Setup](https://github.com/Sydefix/habit-tracker/wiki/Installation-and-Setup)** page on our GitHub Wiki.

## Basic Usage

Here are a few of the most common commands.

-   **Add a new habit:**
    ```bash
    habit add "Read a Book" -p daily
    ```

-   **Checkoff a habit:**
    ```bash
    habit checkoff "Read a Book"
    ```

-   **List all habits:**
    ```bash
    habit list
    ```

-   **Analyze your habits:**
    ```bash
    habit analyze --show summary
    ```

For a complete list of all commands and their options, please see the **[User Guide](https://github.com/Sydefix/habit-tracker/wiki/User-Guide-Command-Line-Usage)** on our GitHub Wiki.

## Contributing

Contributions are welcome! This project is built with a clean, decoupled architecture that is easy to extend.

To get started with development, please see the **[Developer Guide](https://github.com/Sydefix/habit-tracker/wiki/Developer-Guide-&-Project-Architecture)**.

To run the test suite:
```bash
pytest
```
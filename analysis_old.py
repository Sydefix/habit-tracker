


from sqlalchemy.orm import Session
from models import Habit, Completion
from datetime import date, timedelta, datetime
from typing import List, Tuple, Optional, Dict, Any, Union




class HabitAnalysis:
    def __init__(self, db_session: Session):
        self.session = db_session

    def _get_filtered_completion_dates(
        self,
        habit: Habit,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[date]:
        """
        Retrieves and filters unique, sorted completion dates for a habit
        within a given date range.
        
        Return:
            A list of sorted, unique datetime.date objects
        """
        query = self.session.query(Completion.completion_date).filter(
            Completion.habit_id == habit.id
        )
        
        # fitler results by date range
        if start_date:
            query = query.filter(
                Completion.completion_date
                >= datetime.combine(start_date, datetime.min.time())
            )
        if end_date:
            query = query.filter(
                Completion.completion_date
                <= datetime.combine(end_date, datetime.max.time())
            )

        completion_datetimes = [dt[0] for dt in query.all()]
        unique_dates = sorted(list(set(dt.date() for dt in completion_datetimes)))
        return unique_dates

    def _calculate_metrics_from_dates(
        self, completion_dates: List[date]
    ) -> Tuple[int, int, int]:
        """
        Calculates longest streak, number of gaps, and total gap days
        from a list of sorted unique completion dates.

        Args:
            completion_dates: A list of sorted, unique datetime.date objects.

        Returns:
            Tuple[int, int, int]: (longest_streak, num_gaps, total_gap_days)
        """
        if not completion_dates:
            return 0, 0, 0
        if len(completion_dates) == 1:
            return 1, 0, 0

        max_streak = 1
        current_streak = 1
        num_gaps = 0
        total_gap_days = 0

        for i in range(1, len(completion_dates)):
            day_difference = (completion_dates[i] - completion_dates[i - 1]).days
            if day_difference == 1:
                current_streak += 1
            else:  # A gap occurred (day_difference > 1)
                max_streak = max(max_streak, current_streak)
                current_streak = 1  # Reset streak for the new day
                num_gaps += 1
                total_gap_days += day_difference - 1 # The actual number of missed days

        max_streak = max(max_streak, current_streak) # Account for the last streak
        return max_streak, num_gaps, total_gap_days

    def _resolve_habit(self, identifier: Union[int, str, Habit]) -> Optional[Habit]:
        """Helper to get a Habit object from ID, name, or if it's already a Habit object."""
        if isinstance(identifier, Habit):
            # If it's already a Habit object, ensure it's part of the current session
            # or can be merged. For simplicity, we assume it's usable as is if passed.
            # A more robust approach might involve self.session.merge(identifier) if it could be detached.
            return identifier
        elif isinstance(identifier, int):
            return self.session.get(Habit, identifier)
        elif isinstance(identifier, str):
            try:
                # This assumes unique names. If names are not unique, this could be an issue.
                return (
                    self.session.query(Habit)
                    .filter(Habit.name == identifier)
                    .one_or_none()
                )
            except Exception: # Catches MultipleResultsFound from .one_or_none() if not unique
                # Log this or handle as per specific requirements for non-unique names
                return None
        return None

    # --- Individual Habit Metric Methods ---

    def get_longest_streak_for_habit(
        self,
        habit_identifier: Union[int, str, Habit],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        """
        Calculates the longest streak of consecutive daily completions for a specific habit
        within an optional date range.
        """
        habit = self._resolve_habit(habit_identifier)
        if not habit:
            return 0
        completion_dates = self._get_filtered_completion_dates(
            habit, start_date, end_date
        )
        longest_streak, _, _ = self._calculate_metrics_from_dates(completion_dates)
        return longest_streak

    def get_completion_dates_for_habit(
        self,
        habit_identifier: Union[int, str, Habit],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[date]:
        """
        Returns a sorted list of unique completion dates for a specific habit
        within an optional date range.
        """
        habit = self._resolve_habit(habit_identifier)
        if not habit:
            return []
        return self._get_filtered_completion_dates(habit, start_date, end_date)


    def get_number_of_gaps_for_habit(
        self,
        habit_identifier: Union[int, str, Habit],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        """
        Calculates the number of times a streak was broken for a specific habit
        within an optional date range.
        """
        habit = self._resolve_habit(habit_identifier)
        if not habit:
            return 0
        completion_dates = self._get_filtered_completion_dates(
            habit, start_date, end_date
        )
        _, num_gaps, _ = self._calculate_metrics_from_dates(completion_dates)
        return num_gaps

    def get_total_gap_days_for_habit(
        self,
        habit_identifier: Union[int, str, Habit],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        """
        Calculates the total duration of all gaps (pauses) for a specific habit
        within an optional date range.
        """
        habit = self._resolve_habit(habit_identifier)
        if not habit:
            return 0
        completion_dates = self._get_filtered_completion_dates(
            habit, start_date, end_date
        )
        _, _, total_gap_days = self._calculate_metrics_from_dates(completion_dates)
        return total_gap_days

    # --- Overall Analysis Methods ---

    def get_all_tracked_habits(self) -> List[Habit]:
        """Returns a list of all currently tracked habits."""
        return self.session.query(Habit).all()

    def get_longest_streak_overall(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Tuple[Optional[Habit], int]:
        """
        Finds the habit with the longest continuous streak of completions across all habits
        within an optional date range.
        """
        all_habits = self.get_all_tracked_habits()
        if not all_habits:
            return None, 0

        overall_longest_streak_val = 0
        habit_with_longest_streak = None

        for habit in all_habits:
            current_habit_longest_streak = self.get_longest_streak_for_habit(
                habit, start_date, end_date
            )
            if current_habit_longest_streak > overall_longest_streak_val:
                overall_longest_streak_val = current_habit_longest_streak
                habit_with_longest_streak = habit
        return habit_with_longest_streak, overall_longest_streak_val

    def get_habits_completed_on_date(self, target_date: date) -> List[Habit]:
        """
        Returns a list of habits that have at least one completion on the given target_date.
        """
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())

        completed_habit_ids = (
            self.session.query(Completion.habit_id)
            .filter(Completion.completion_date >= start_datetime)
            .filter(Completion.completion_date <= end_datetime)
            .distinct()
            .all()
        )
        habit_ids = [hid[0] for hid in completed_habit_ids]
        if not habit_ids:
            return []
        return self.session.query(Habit).filter(Habit.id.in_(habit_ids)).all()

    def get_most_struggled_habits(
        self,
        top_n: int = 5,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Identifies habits with the most "struggle" within a given period.
        Struggle score = number_of_gaps + total_gap_days.
        Returns a list of dictionaries with habit info and score.
        """
        all_habits = self.get_all_tracked_habits()
        if not all_habits:
            return []

        struggle_data = []
        for habit in all_habits:
            num_gaps = self.get_number_of_gaps_for_habit(
                habit, start_date, end_date
            )
            total_gap_days = self.get_total_gap_days_for_habit(
                habit, start_date, end_date
            )
            score = float(num_gaps + total_gap_days)

            if score > 0: # Only include habits with actual struggle
                struggle_data.append(
                    {
                        "habit_id": habit.id,
                        "habit_name": habit.name,
                        "struggle_score": score,
                        "gaps": num_gaps,
                        "gap_days": total_gap_days,
                    }
                )
        struggle_data.sort(key=lambda x: x["struggle_score"], reverse=True)
        return struggle_data[:top_n]

    # --- Summary Method ---
    def summary(self) -> Dict[str, Any]:
        """
        Provides a comprehensive summary of habit analytics.
        """
        today = date.today()
        one_month_ago = today - timedelta(days=30) # Approx. last month

        all_habits_list = self.get_all_tracked_habits()
        (
            longest_overall_habit_obj,
            longest_overall_streak_val,
        ) = self.get_longest_streak_overall()

        habits_completed_today_list = self.get_habits_completed_on_date(today)

        struggled_last_month = self.get_most_struggled_habits(
            top_n=5, start_date=one_month_ago, end_date=today
        )

        individual_streaks = []
        for habit in all_habits_list:
            streak = self.get_longest_streak_for_habit(habit)
            if streak > 0: # Only include habits with some streak
                individual_streaks.append(
                    {"habit_name": habit.name, "longest_streak": streak}
                )
        individual_streaks.sort(key=lambda x: x["longest_streak"], reverse=True)


        summary_data = {
            "total_tracked_habits": len(all_habits_list),
            "all_habits_names": [h.name for h in all_habits_list],
            "current_daily_habits_active_today": [
                h.name for h in habits_completed_today_list
            ],
            "longest_streak_all_habits": {
                "habit_name": longest_overall_habit_obj.name
                if longest_overall_habit_obj
                else None,
                "streak_days": longest_overall_streak_val,
            },
            "longest_streak_per_habit": individual_streaks,
            "most_struggled_habits_last_month": struggled_last_month,
            # "habits_by_periodicity": "This feature requires a 'periodicity' field in the Habit model."
        }
        # The "habits with the same periodicity" is still best addressed if you add
        # a 'periodicity' (e.g., 'daily', 'weekly') field to your Habit model.
        # Then you could easily query and group by it.
        # For now, 'current_daily_habits_active_today' serves as a proxy.

        return summary_data
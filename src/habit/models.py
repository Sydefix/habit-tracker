"""
Defines the database schema for the Habit Tracker application.

This module contains the SQLAlchemy ORM models for the 'Habit' and
'Completion' tables, establishing their columns, attributes, and the
relationship between them.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

# Create a base class for declarative models
Base = declarative_base()


class Habit(Base):
    """Represents a single habit tracked by a user."""

    __tablename__ = "habits"

    #: Unique identifier for the habit.
    id = Column(Integer, primary_key=True, index=True)
    #: The name of the habit (e.g., 'Drink Water').
    name = Column(String, index=True, nullable=False)
    #: A short description of the habit.
    description = Column(String)
    #: The frequency of the habit ('daily', 'weekly', 'monthly').
    periodicity = Column(String, nullable=False, default="daily")
    #: The timestamp when the habit was created.
    creation_date = Column(DateTime, default=datetime.now, nullable=False)

    #: A one-to-many relationship to all associated completion records.
    #: Deleting a habit will also delete all its completions.
    completions = relationship(
        "Completion", back_populates="habit", cascade="all, delete-orphan"
    )

    def __repr__(self):
        """Provides a developer-friendly string representation of the habit."""
        return (
            f"<Habit(id={self.id}, name='{self.name}', "
            f"creation_date='{self.creation_date.strftime('%Y-%m-%d %H:%M:%S')}')>"
        )


class Completion(Base):
    """Represents a single completion event for a specific habit."""

    __tablename__ = "completions"

    #: Unique identifier for the completion event.
    id = Column(Integer, primary_key=True, index=True)
    #: The timestamp when the habit was marked as complete.
    completion_date = Column(DateTime, nullable=False)
    #: A foreign key linking this completion to a specific habit.
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)

    #: A many-to-one relationship back to the parent Habit object.
    habit = relationship("Habit", back_populates="completions")

    def __repr__(self):
        """Provides a developer-friendly string representation of the completion."""
        return (
            f"<Completion(id={self.id}, "
            f"completion_date='{self.completion_date.strftime('%Y-%m-%d %H:%M:%S')}', "
            f"habit_id={self.habit_id})>"
        )
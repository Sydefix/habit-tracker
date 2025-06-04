from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

# Create a base class for declarative models
Base = declarative_base()


# Define the Habits table
class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    periodicity = Column(String, nullable=False, default="daily")
    creation_date = Column(DateTime, default=datetime.now, nullable=False)

    completions = relationship(
        "Completion", back_populates="habit", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<Habit(id={self.id}, name='{self.name}', "
            f"creation_date='{self.creation_date.strftime('%Y-%m-%d %H:%M:%S')}')>"
        )


# Define the Completions table
class Completion(Base):
    __tablename__ = "completions"

    id = Column(Integer, primary_key=True, index=True)
    completion_date = Column(DateTime, nullable=False)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)

    habit = relationship("Habit", back_populates="completions")

    def __repr__(self):
        return (
            f"<Completion(id={self.id}, "
            f"completion_date='{self.completion_date.strftime('%Y-%m-%d %H:%M:%S')}', "
            f"habit_id={self.habit_id})>"
        )
        


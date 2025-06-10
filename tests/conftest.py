import pytest
from typing import Iterator
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession

from habit.models import Base, Habit
from habit.habit_manager import HabitManager


@pytest.fixture(scope="session")
def engine():
    """
    Creates an in-memory SQLite engine for the entire test session.
    The database exists only for the duration of the test session.
    """
    return create_engine("sqlite:///:memory:")


@pytest.fixture(scope="session")
def setup_database(engine):
    """
    Creates all tables in the database. This runs once per test session.
    """
    Base.metadata.create_all(bind=engine)
    yield
    # Optional: Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine, setup_database) -> Iterator[SQLAlchemySession]:
    """
    Provides a clean database session for a single test function.

    This fixture creates a new connection and transaction for each test,
    and rolls back the transaction after the test completes, ensuring
    perfect test isolation.
    """
    connection = engine.connect()
    transaction = connection.begin()
    TestSessionLocal = sessionmaker(bind=connection)
    session = TestSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def habit_manager(db_session: SQLAlchemySession) -> HabitManager:
    """
    Provides an instance of HabitManager initialized with a clean db_session
    for a single test function.
    """
    return HabitManager(session=db_session)
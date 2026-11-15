"""SQLite persistence for the user's completed generated activities."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select

DB_PATH = Path(__file__).resolve().parent.parent / "kairos.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


class CompletedActivity(SQLModel, table=True):
    __tablename__ = "completed_activities"

    id: Optional[int] = Field(default=None, primary_key=True)
    activity_id: str
    title: str
    category_tag: str
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def add_completed(activity_id: str, title: str, category_tag: str) -> CompletedActivity:
    row = CompletedActivity(activity_id=activity_id, title=title, category_tag=category_tag)
    with Session(engine) as session:
        session.add(row)
        session.commit()
        session.refresh(row)
    return row


def list_completed() -> list[CompletedActivity]:
    with Session(engine) as session:
        return list(session.exec(select(CompletedActivity).order_by(CompletedActivity.completed_at.desc())).all())

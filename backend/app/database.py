"""SQLite + SQLModel : table `activities`."""
from pathlib import Path
from typing import Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, Session, SQLModel, create_engine, select

DB_PATH = Path(__file__).resolve().parent.parent / "kairos.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


class Activity(SQLModel, table=True):
    __tablename__ = "activities"

    id: str = Field(primary_key=True)
    type: str  # indoor / outdoor
    category: str  # outdoor / creative / intellectual
    category_tag: str
    title: str
    description: str
    location_tag: str
    image_url: str
    maps_url: Optional[str] = None
    vibe_tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    is_social: bool = False  # True = adapté à plusieurs
    solo_ok: bool = True
    instructions: list[str] = Field(default_factory=list, sa_column=Column(JSON))


def init_db() -> None:
    from .seed_data import ACTIVITIES

    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        if s.exec(select(Activity)).first() is None:
            s.add_all(Activity(**a) for a in ACTIVITIES)
            s.commit()


def all_activities() -> list[Activity]:
    with Session(engine) as s:
        return list(s.exec(select(Activity)).all())

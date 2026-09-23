from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.services.system_metadata import (
    create_metadata,
    delete_metadata,
    get_metadata,
    update_metadata,
)


def test_system_metadata_crud() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        metadata = create_metadata(db, key="schema_version", value="1")
        assert metadata.id is not None
        assert get_metadata(db, key="schema_version") is metadata

        updated = update_metadata(db, metadata, value="2")
        assert updated.value == "2"

        delete_metadata(db, metadata)
        assert get_metadata(db, key="schema_version") is None

"""CRUD operations for temporary system metadata."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.system_metadata import SystemMetadata


def create_metadata(db: Session, *, key: str, value: str) -> SystemMetadata:
    metadata = SystemMetadata(key=key, value=value)
    db.add(metadata)
    db.commit()
    db.refresh(metadata)
    return metadata


def get_metadata(db: Session, *, key: str) -> SystemMetadata | None:
    return db.scalar(select(SystemMetadata).where(SystemMetadata.key == key))


def update_metadata(
    db: Session,
    metadata: SystemMetadata,
    *,
    value: str,
) -> SystemMetadata:
    metadata.value = value
    db.commit()
    db.refresh(metadata)
    return metadata


def delete_metadata(db: Session, metadata: SystemMetadata) -> None:
    db.delete(metadata)
    db.commit()

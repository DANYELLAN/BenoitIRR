from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class InspectionRecord(Base):
    __tablename__ = 'inspection_records'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    work_order: Mapped[str] = mapped_column(String(64), index=True)
    connection: Mapped[str] = mapped_column(String(128), index=True)
    pipe_number: Mapped[int] = mapped_column(Integer, index=True)
    inspection_round: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default='FIRST_INSPECTION')
    inspector_adp: Mapped[str] = mapped_column(String(32), index=True)
    inspector_name: Mapped[str] = mapped_column(String(128))
    operator_name: Mapped[str] = mapped_column(String(128))
    area: Mapped[str] = mapped_column(String(64))
    machine_number: Mapped[str] = mapped_column(String(64))
    shift: Mapped[str] = mapped_column(String(32))
    fai_number: Mapped[str] = mapped_column(String(64))
    drawing_number: Mapped[str] = mapped_column(String(64))
    measurements: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ncr: Mapped['NCRRecord | None'] = relationship(back_populates='inspection', uselist=False)


class NCRRecord(Base):
    __tablename__ = 'ncr_records'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inspection_id: Mapped[int] = mapped_column(ForeignKey('inspection_records.id'), unique=True)
    tier_code: Mapped[str] = mapped_column(String(16))
    nonconformance: Mapped[str] = mapped_column(Text)
    immediate_containment: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default='OPEN')

    inspection: Mapped['InspectionRecord'] = relationship(back_populates='ncr')

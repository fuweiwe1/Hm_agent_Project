import csv
from typing import Optional

from sqlalchemy import Column, String, create_engine, text
from sqlalchemy.orm import Session, declarative_base

from repositories.business_repository import UsageRecordRow
from utils.config_handler import business_conf

Base = declarative_base()


class UsageRecordOrm(Base):
    __tablename__ = "usage_records"
    user_id = Column(String, primary_key=True)
    month = Column(String, primary_key=True)
    feature = Column(String)
    efficiency = Column(String)
    consumables = Column(String)
    comparison = Column(String)


class PostgreSQLBusinessRepository:
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or business_conf["database_url"]
        self.seed_csv_path = business_conf["seed_csv_path"]
        self.engine = create_engine(self.db_url, pool_pre_ping=True)
        self._initialize_database()

    def _initialize_database(self) -> None:
        Base.metadata.create_all(self.engine)
        self._seed_if_needed()

    def _seed_if_needed(self) -> None:
        with Session(self.engine) as session:
            if session.query(UsageRecordOrm).count() > 0:
                return
        self._import_seed_data()

    def _import_seed_data(self) -> None:
        with open(self.seed_csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            next(reader, None)
            rows = []
            for row in reader:
                if len(row) < 6:
                    continue
                rows.append(UsageRecordOrm(
                    user_id=row[0], month=row[5],
                    feature=row[1], efficiency=row[2],
                    consumables=row[3], comparison=row[4],
                ))
        with Session(self.engine) as session:
            session.add_all(rows)
            session.commit()

    def list_user_ids(self) -> list[str]:
        with Session(self.engine) as session:
            rows = session.query(UsageRecordOrm.user_id).distinct().order_by(UsageRecordOrm.user_id).all()
        return [r.user_id for r in rows]

    def list_available_months(self, user_id: str) -> list[str]:
        with Session(self.engine) as session:
            rows = session.query(UsageRecordOrm.month).filter(
                UsageRecordOrm.user_id == user_id
            ).order_by(UsageRecordOrm.month).all()
        return [r.month for r in rows]

    def get_usage_record(self, user_id: str, month: str) -> Optional[UsageRecordRow]:
        with Session(self.engine) as session:
            row = session.query(UsageRecordOrm).filter(
                UsageRecordOrm.user_id == user_id,
                UsageRecordOrm.month == month,
            ).first()
        return self._to_row(row)

    def get_latest_usage_record(self, user_id: str) -> Optional[UsageRecordRow]:
        with Session(self.engine) as session:
            row = session.query(UsageRecordOrm).filter(
                UsageRecordOrm.user_id == user_id
            ).order_by(UsageRecordOrm.month.desc()).first()
        return self._to_row(row)

    @staticmethod
    def _to_row(orm: UsageRecordOrm | None) -> Optional[UsageRecordRow]:
        if orm is None:
            return None
        return UsageRecordRow(
            user_id=orm.user_id,
            month=orm.month,
            feature=orm.feature,
            efficiency=orm.efficiency,
            consumables=orm.consumables,
            comparison=orm.comparison,
        )

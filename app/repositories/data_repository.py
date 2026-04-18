"""Load FSTEC incidents and threat registry: prefer DB tables, else Excel or in-process fallback."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time as dt_time
from functools import lru_cache
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.models import FstecThreat, Incident, Organization


@dataclass(frozen=True)
class IncidentQueryFilters:
    """Incident filters for SQL (incidents table) and the mirrored Excel fallback path."""

    season: str | None = None
    region: str | None = None
    industry: str | None = None
    success: int | None = None
    time_of_day: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    threat_code: int | None = None

    def has_any(self) -> bool:
        return any(
            [
                self.season is not None,
                self.region is not None,
                self.industry is not None,
                self.success is not None,
                self.time_of_day is not None,
                self.date_from is not None,
                self.date_to is not None,
                self.threat_code is not None,
            ]
        )

BASE_DIR = Path(__file__).resolve().parents[2]


def _locate_data_file(filename: str) -> Path:
    candidates = [
        BASE_DIR / 'data' / filename,
        BASE_DIR / filename,
        BASE_DIR.parent / filename,
        BASE_DIR.parent.parent / filename,
        Path('/mnt/data') / filename,
        ]

    for candidate in candidates:
        try:
            if candidate.exists():
                return candidate
        except Exception:
            continue

    return candidates[0]


INCIDENTS_PATH = _locate_data_file('incidents_2000.xlsx')
FSTEC_PATH = _locate_data_file('thrlist .xlsx')

FALLBACK_INCIDENTS = [
    {
        "Тип предприятия": "telecom",
        "Код предприятия": "org-001",
        "Количество хостов": 1200,
        "Код реализованной угрозы": 101,
        "Успех": 1,
        "Регион размещения предприятия": "Moscow",
        "Дата инцидента": "2026-01-10",
        "Региональное время": "2026-01-10 09:00:00",
    },
    {
        "Тип предприятия": "telecom",
        "Код предприятия": "org-001",
        "Количество хостов": 1200,
        "Код реализованной угрозы": 102,
        "Успех": 1,
        "Регион размещения предприятия": "Moscow",
        "Дата инцидента": "2026-01-11",
        "Региональное время": "2026-01-11 21:00:00",
    },
    {
        "Тип предприятия": "telecom",
        "Код предприятия": "org-001",
        "Количество хостов": 1200,
        "Код реализованной угрозы": 103,
        "Успех": 0,
        "Регион размещения предприятия": "Moscow",
        "Дата инцидента": "2026-03-05",
        "Региональное время": "2026-03-05 06:30:00",
    },
    {
        "Тип предприятия": "finance",
        "Код предприятия": "org-002",
        "Количество хостов": 640,
        "Код реализованной угрозы": 104,
        "Успех": 1,
        "Регион размещения предприятия": "Saint Petersburg",
        "Дата инцидента": "2026-07-20",
        "Региональное время": "2026-07-20 14:15:00",
    },
    {
        "Тип предприятия": "retail",
        "Код предприятия": "org-003",
        "Количество хостов": 220,
        "Код реализованной угрозы": 105,
        "Успех": 0,
        "Регион размещения предприятия": "Novosibirsk",
        "Дата инцидента": "2026-10-01",
        "Региональное время": "2026-10-01 02:40:00",
    },
]

FALLBACK_FSTEC = [
    {
        "Идентификатор УБИ": 101,
        "Наименование УБИ": "Компрометация VPN-доступа",
        "Описание": "Подбор паролей и отсутствие MFA для удаленного доступа.",
        "Объект воздействия": "VPN и сетевые сервисы",
        "Статус угрозы": "Актуальна",
    },
    {
        "Идентификатор УБИ": 102,
        "Наименование УБИ": "Фишинговая рассылка",
        "Описание": "Почтовые сообщения для кражи учетных данных пользователей.",
        "Объект воздействия": "Почта и учетные данные пользователя",
        "Статус угрозы": "Актуальна",
    },
    {
        "Идентификатор УБИ": 103,
        "Наименование УБИ": "Вредоносное ПО на рабочей станции",
        "Описание": "Распространение вредоносного кода через пользовательские устройства.",
        "Объект воздействия": "Рабочая станция",
        "Статус угрозы": "Актуальна",
    },
    {
        "Идентификатор УБИ": 104,
        "Наименование УБИ": "SQL-инъекция веб-портала",
        "Описание": "Атака через небезопасную обработку входных данных веб-приложения.",
        "Объект воздействия": "Веб-портал и СУБД",
        "Статус угрозы": "Актуальна",
    },
    {
        "Идентификатор УБИ": 105,
        "Наименование УБИ": "Шифровальщик файлового сервера",
        "Описание": "Вредоносное шифрование общих папок и файловых хранилищ.",
        "Объект воздействия": "Файловое хранилище",
        "Статус угрозы": "Актуальна",
    },
]


class DataRepository:
    """Normalize datasets and seed domain tables from files."""

    def __init__(self, incidents_path: Path = INCIDENTS_PATH, fstec_path: Path = FSTEC_PATH):
        self.incidents_path = incidents_path
        self.fstec_path = fstec_path

    def load_incidents(self, db: Session | None = None) -> pd.DataFrame:
        """Incidents from the DB when the table has rows, otherwise from file."""
        if db is not None:
            frame = self._load_incidents_from_db(db)
            if not frame.empty:
                return frame
        return self._load_incidents_from_file()

    def load_incidents_by_organization_code(
        self,
        organization_code: str | None,
        db: Session | None = None,
        *,
        incident_filters: IncidentQueryFilters | None = None,
    ) -> pd.DataFrame:
        """Incidents for an organization code; SQL filters when db is set, else Excel + pandas."""
        if db is not None:
            frame = self._query_incidents_from_db(db, organization_code, incident_filters)
            if not frame.empty:
                return frame
        incidents = self._load_incidents_from_file()
        if organization_code:
            incidents = incidents[incidents['organization_code'] == str(organization_code)]
            if incidents.empty:
                return incidents.iloc[0:0].copy()
        return self._apply_filters_pandas(incidents, incident_filters)

    def distinct_incident_facets(self, organization_code: str, db: Session) -> tuple[list[str], list[str]]:
        """Distinct region and industry in the DB for the organization (UI filters)."""
        code = str(organization_code)
        org_row = db.query(Organization).filter(Organization.code == code).first()
        if org_row is None:
            return [], []
        org_id = org_row.id
        regions = sorted(
            {row[0] for row in db.query(Incident.region).filter(Incident.organization_id == org_id).distinct().all() if row[0]}
        )
        industries = sorted(
            {row[0] for row in db.query(Incident.industry).filter(Incident.organization_id == org_id).distinct().all() if row[0]}
        )
        return regions, industries

    def load_fstec_registry(self, db: Session | None = None) -> pd.DataFrame:
        """FSTEC threat registry from the DB or from file."""
        if db is not None:
            frame = self._load_fstec_from_db(db)
            if not frame.empty:
                return frame
        return self._load_fstec_from_file()

    def seed_domain_tables(self, db: Session) -> None:
        """One-shot seed: FSTEC registry, organizations from incident file, then incidents (FK-safe order)."""
        incidents_frame = self._load_incidents_from_file()

        if db.query(FstecThreat).first() is None:
            registry = self._load_fstec_from_file()
            fstec_records = [
                FstecThreat(
                    threat_code=int(row["threat_code"]),
                    name=str(row["name"]),
                    description=str(row["description"]),
                    source_characteristics=None if pd.isna(row.get("source_characteristics")) else str(row["source_characteristics"]),
                    object_of_impact=None if pd.isna(row.get("object_of_impact")) else str(row["object_of_impact"]),
                    confidentiality_breach=int(row.get("confidentiality_breach", 0) or 0),
                    integrity_breach=int(row.get("integrity_breach", 0) or 0),
                    availability_breach=int(row.get("availability_breach", 0) or 0),
                    date_added=row["date_added"].to_pydatetime() if pd.notna(row.get("date_added")) else None,
                    last_modified=row["last_modified"].to_pydatetime() if pd.notna(row.get("last_modified")) else None,
                    status=None if pd.isna(row.get("status")) else str(row["status"]),
                    notes=None if pd.isna(row.get("notes")) else str(row["notes"]),
                )
                for _, row in registry.iterrows()
                if pd.notna(row["threat_code"])
            ]
            db.add_all(fstec_records)
            db.commit()

        if incidents_frame.empty:
            return

        for code in sorted(incidents_frame["organization_code"].dropna().astype(str).unique().tolist()):
            if not db.query(Organization).filter(Organization.code == code).first():
                db.add(Organization(name=f"Organization {code}", code=code))
        db.commit()

        org_by_code = {str(o.code): o.id for o in db.query(Organization).all() if o.code}

        if db.query(Incident).first() is None:
            records = []
            for _, row in incidents_frame.iterrows():
                code = str(row["organization_code"])
                org_id = org_by_code.get(code)
                if org_id is None:
                    continue
                records.append(
                    Incident(
                        organization_id=org_id,
                        organization_code=code,
                        industry=str(row["industry"]),
                        host_count=int(row["host_count"]),
                        threat_code=int(row["threat_code"]),
                        success=int(row["success"]),
                        region=str(row["region"]),
                        incident_date=row["incident_date"].to_pydatetime() if pd.notna(row["incident_date"]) else None,
                        regional_time=row["regional_time"].to_pydatetime() if pd.notna(row["regional_time"]) else None,
                        hour=int(row["hour"]),
                        month=int(row["month"]),
                        season=str(row["season"]),
                        time_of_day=str(row["time_of_day"]),
                        day_of_week=int(row["day_of_week"]),
                    )
                )
            db.add_all(records)
            db.commit()

    @lru_cache(maxsize=1)
    def _load_incidents_from_file(self) -> pd.DataFrame:
        if self.incidents_path.exists():
            frame = pd.read_excel(self.incidents_path)
        else:
            frame = pd.DataFrame(FALLBACK_INCIDENTS)
        return self._normalize_incidents(frame)

    @staticmethod
    def _incident_rows_to_dataframe(rows: list[Incident]) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(
            [
                {
                    "organization_id": row.organization_id,
                    "organization_code": row.organization_code,
                    "industry": row.industry,
                    "host_count": row.host_count,
                    "threat_code": row.threat_code,
                    "success": row.success,
                    "region": row.region,
                    "incident_date": row.incident_date,
                    "regional_time": row.regional_time,
                    "hour": row.hour,
                    "month": row.month,
                    "season": row.season,
                    "time_of_day": row.time_of_day,
                    "day_of_week": row.day_of_week,
                }
                for row in rows
            ]
        )

    def _query_incidents_from_db(
        self,
        db: Session,
        organization_code: str | None,
        filters: IncidentQueryFilters | None,
    ) -> pd.DataFrame:
        q = db.query(Incident)
        if organization_code:
            org_row = db.query(Organization).filter(Organization.code == str(organization_code)).first()
            if org_row is not None:
                q = q.filter(Incident.organization_id == org_row.id)
            else:
                q = q.filter(Incident.organization_code == str(organization_code))
        if filters is not None:
            if filters.season is not None:
                q = q.filter(Incident.season == filters.season)
            if filters.region is not None:
                q = q.filter(Incident.region == filters.region)
            if filters.industry is not None:
                q = q.filter(Incident.industry == filters.industry)
            if filters.success is not None:
                q = q.filter(Incident.success == filters.success)
            if filters.time_of_day is not None:
                q = q.filter(Incident.time_of_day == filters.time_of_day)
            if filters.date_from is not None:
                q = q.filter(Incident.incident_date >= datetime.combine(filters.date_from, dt_time.min))
            if filters.date_to is not None:
                q = q.filter(Incident.incident_date <= datetime.combine(filters.date_to, dt_time.max))
            if filters.threat_code is not None:
                q = q.filter(Incident.threat_code == filters.threat_code)
        rows = q.order_by(Incident.id.asc()).all()
        return self._incident_rows_to_dataframe(rows)

    @staticmethod
    def _apply_filters_pandas(df: pd.DataFrame, filters: IncidentQueryFilters | None) -> pd.DataFrame:
        if df.empty or filters is None or not filters.has_any():
            return df
        out = df
        if filters.season is not None:
            out = out[out["season"] == filters.season]
        if filters.region is not None:
            out = out[out["region"] == filters.region]
        if filters.industry is not None:
            out = out[out["industry"] == filters.industry]
        if filters.success is not None:
            out = out[out["success"] == filters.success]
        if filters.time_of_day is not None:
            out = out[out["time_of_day"] == filters.time_of_day]
        if filters.threat_code is not None:
            out = out[out["threat_code"] == filters.threat_code]
        if filters.date_from is not None:
            ts = pd.Timestamp(filters.date_from)
            out = out[out["incident_date"].notna() & (out["incident_date"] >= ts)]
        if filters.date_to is not None:
            ts_end = pd.Timestamp(filters.date_to) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
            out = out[out["incident_date"].notna() & (out["incident_date"] <= ts_end)]
        return out

    @staticmethod
    def _load_incidents_from_db(db: Session) -> pd.DataFrame:
        rows = db.query(Incident).order_by(Incident.id.asc()).all()
        return DataRepository._incident_rows_to_dataframe(rows)

    @lru_cache(maxsize=1)
    def _load_fstec_from_file(self) -> pd.DataFrame:
        if self.fstec_path.exists():
            raw = pd.read_excel(self.fstec_path, header=None)
            header_idx = 0
            expected = "Идентификатор УБИ"
            for idx in range(min(5, len(raw))):
                candidate = [str(value).strip() for value in raw.iloc[idx].tolist()]
                if expected in candidate:
                    header_idx = idx
                    break
            frame = raw.iloc[header_idx + 1 :].reset_index(drop=True)
            frame.columns = raw.iloc[header_idx].tolist()
        else:
            frame = pd.DataFrame(FALLBACK_FSTEC)
        return self._normalize_fstec(frame)

    @staticmethod
    def _load_fstec_from_db(db: Session) -> pd.DataFrame:
        rows = db.query(FstecThreat).order_by(FstecThreat.threat_code.asc()).all()
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(
            [
                {
                    "threat_code": row.threat_code,
                    "name": row.name,
                    "description": row.description,
                    "source_characteristics": row.source_characteristics,
                    "object_of_impact": row.object_of_impact,
                    "confidentiality_breach": row.confidentiality_breach,
                    "integrity_breach": row.integrity_breach,
                    "availability_breach": row.availability_breach,
                    "date_added": row.date_added,
                    "last_modified": row.last_modified,
                    "status": row.status,
                    "notes": row.notes,
                }
                for row in rows
            ]
        )

    def _normalize_incidents(self, frame: pd.DataFrame) -> pd.DataFrame:
        frame = frame.rename(
            columns={
                "Тип предприятия": "industry",
                "Код предприятия": "organization_code",
                "Количество хостов": "host_count",
                "Код реализованной угрозы": "threat_code",
                "Успех": "success",
                "Регион размещения предприятия": "region",
                "Дата инцидента": "incident_date",
                "Региональное время": "regional_time",
            }
        )
        frame["organization_code"] = frame["organization_code"].astype(str)
        frame["incident_date"] = pd.to_datetime(frame["incident_date"], errors="coerce", dayfirst=True)
        frame["regional_time"] = pd.to_datetime(frame["regional_time"], errors="coerce", dayfirst=True)
        frame["hour"] = frame["regional_time"].dt.hour.fillna(0).astype(int)
        frame["month"] = frame["incident_date"].dt.month.fillna(1).astype(int)
        frame["season"] = frame["month"].map(
            {
                12: "winter",
                1: "winter",
                2: "winter",
                3: "spring",
                4: "spring",
                5: "spring",
                6: "summer",
                7: "summer",
                8: "summer",
                9: "autumn",
                10: "autumn",
                11: "autumn",
            }
        )
        frame["time_of_day"] = frame["hour"].map(self._time_of_day)
        frame["day_of_week"] = frame["incident_date"].dt.isocalendar().day.fillna(1).astype(int)
        return frame

    @staticmethod
    def _normalize_fstec(frame: pd.DataFrame) -> pd.DataFrame:
        frame = frame.rename(
            columns={
                "Идентификатор УБИ": "threat_code",
                "Наименование УБИ": "name",
                "Описание": "description",
                "Источник угрозы (характеристика и потенциал нарушителя)": "source_characteristics",
                "Объект воздействия": "object_of_impact",
                "Нарушение конфиденциальности": "confidentiality_breach",
                "Нарушение целостности": "integrity_breach",
                "Нарушение доступности": "availability_breach",
                "Дата включения угрозы в БнД УБИ": "date_added",
                "Дата последнего изменения данных": "last_modified",
                "Статус угрозы": "status",
                "Замечания": "notes",
            }
        )
        frame["threat_code"] = pd.to_numeric(frame["threat_code"], errors="coerce").astype("Int64")
        for column in ("confidentiality_breach", "integrity_breach", "availability_breach"):
            if column in frame.columns:
                frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0).astype(int)
        for column in ("date_added", "last_modified"):
            if column in frame.columns:
                frame[column] = pd.to_datetime(frame[column], errors="coerce")
        return frame

    @staticmethod
    def _time_of_day(hour: int) -> str:
        if 0 <= hour <= 5:
            return 'night'
        if 6 <= hour <= 11:
            return 'morning'
        if 12 <= hour <= 17:
            return 'afternoon'
        return 'evening'


@lru_cache(maxsize=1)
def get_data_repository() -> DataRepository:
    """Process-wide singleton DataRepository."""
    return DataRepository()

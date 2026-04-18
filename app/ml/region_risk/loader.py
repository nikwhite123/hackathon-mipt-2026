"""Load incidents and threat registry in the same shape used by the notebook."""

from __future__ import annotations

import io
import re
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"

INCIDENTS_COLUMNS = [
    "Тип предприятия",
    "Код предприятия",
    "Количество хостов",
    "Код реализованной угрозы",
    "Успех",
    "Регион размещения предприятия",
    "Дата инцидента",
    "Региональное время",
]
INCIDENTS_REQUIRED = set(INCIDENTS_COLUMNS)

THREAT_COLUMNS = [
    "Идентификатор УБИ",
    "Наименование УБИ",
    "Описание",
    "Источник угрозы (характеристика и потенциал нарушителя)",
    "Объект воздействия",
    "Нарушение конфиденциальности",
    "Нарушение целостности",
    "Нарушение доступности",
    "Дата включения угрозы в БнД УБИ",
    "Дата последнего изменения данных",
    "Статус угрозы",
    "Замечания",
]
THREAT_REQUIRED = {
    "Идентификатор УБИ",
    "Наименование УБИ",
    "Источник угрозы (характеристика и потенциал нарушителя)",
    "Объект воздействия",
    "Нарушение конфиденциальности",
    "Нарушение целостности",
    "Нарушение доступности",
}


def _locate_first_existing(*candidates: str) -> Path:
    for candidate in candidates:
        path = DATA_DIR / candidate
        if path.exists():
            return path
    return DATA_DIR / candidates[0]


DEFAULT_INCIDENTS_PATH = _locate_first_existing("incidents_2000.xlsx")
DEFAULT_THREATLIST_PATH = _locate_first_existing("thrlist .xlsx", "Файл с сайта ФСТЭК.xlsx")


def normalize_columns(columns: list[object] | pd.Index) -> list[str]:
    return [re.sub(r"\s+", " ", str(c).strip()) for c in columns]


def read_table(path: Path, *, no_header: bool = False, manual_columns: list[str] | None = None) -> pd.DataFrame:
    """Read Excel or CSV and optionally assign known columns for headerless data."""
    file_bytes = path.read_bytes()
    lower_name = path.name.lower()

    if lower_name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(file_bytes), header=None if no_header else 0)
        if no_header and manual_columns is not None:
            if df.shape[1] != len(manual_columns):
                raise ValueError(f"{path.name}: expected {len(manual_columns)} columns, got {df.shape[1]}")
            df.columns = manual_columns
        return df

    encodings = ["utf-8", "utf-8-sig", "cp1251", "latin1"]
    separators = [None, ";", ",", "\t"]
    last_error: Exception | None = None

    for encoding in encodings:
        for separator in separators:
            try:
                df = pd.read_csv(
                    io.BytesIO(file_bytes),
                    encoding=encoding,
                    sep=separator,
                    engine="python" if separator is None else "c",
                    header=None if no_header else 0,
                )
                if no_header and manual_columns is not None:
                    if df.shape[1] != len(manual_columns):
                        continue
                    df.columns = manual_columns
                if df.shape[1] > 1:
                    return df
            except Exception as exc:  # pragma: no cover - best effort for local files
                last_error = exc

    raise ValueError(f"Could not read {path.name}. Last error: {last_error}")


def _read_incidents_sheet(path: Path) -> pd.DataFrame:
    raw = read_table(path, no_header=True)
    for header_idx in range(min(3, len(raw))):
        candidate_columns = normalize_columns(raw.iloc[header_idx].tolist())
        if INCIDENTS_REQUIRED.issubset(set(candidate_columns)):
            frame = raw.iloc[header_idx + 1 :].copy()
            frame.columns = candidate_columns
            return frame.reset_index(drop=True)
    raise ValueError(f"Could not find incidents header row in {path}")


def _read_threat_sheet(path: Path) -> pd.DataFrame:
    raw = read_table(path, no_header=True)
    for header_idx in range(min(5, len(raw))):
        candidate_columns = normalize_columns(raw.iloc[header_idx].tolist())
        if THREAT_REQUIRED.issubset(set(candidate_columns)):
            frame = raw.iloc[header_idx + 1 :].copy()
            frame.columns = candidate_columns
            return frame.reset_index(drop=True)
    raise ValueError(f"Could not find threat header row in {path}")


def prepare_data_from_paths(
    incidents_path: Path = DEFAULT_INCIDENTS_PATH,
    threatlist_path: Path = DEFAULT_THREATLIST_PATH,
) -> pd.DataFrame:
    """Notebook-style merged dataset prepared from the raw Excel files."""
    incidents = _read_incidents_sheet(incidents_path).copy()
    threatlist = _read_threat_sheet(threatlist_path).copy()

    incidents = incidents.rename(
        columns={
            "Тип предприятия": "org_type",
            "Код предприятия": "enterprise_code",
            "Количество хостов": "host_count",
            "Код реализованной угрозы": "threat_code",
            "Успех": "success",
            "Регион размещения предприятия": "region",
            "Дата инцидента": "incident_date",
            "Региональное время": "regional_time",
        }
    )
    threatlist = threatlist.rename(
        columns={
            "Идентификатор УБИ": "threat_code",
            "Наименование УБИ": "threat_name",
            "Источник угрозы (характеристика и потенциал нарушителя)": "threat_source",
            "Объект воздействия": "impact_object",
            "Нарушение конфиденциальности": "confidentiality_violation",
            "Нарушение целостности": "integrity_violation",
            "Нарушение доступности": "availability_violation",
        }
    )

    return _merge_notebook_frames(incidents, threatlist)


def _normalize_registry_frame(registry: pd.DataFrame) -> pd.DataFrame:
    frame = registry.copy()
    frame = frame.rename(
        columns={
            "name": "threat_name",
            "source_characteristics": "threat_source",
            "object_of_impact": "impact_object",
            "confidentiality_breach": "confidentiality_violation",
            "integrity_breach": "integrity_violation",
            "availability_breach": "availability_violation",
            "description": "description",
        }
    )
    return frame


def _normalize_incidents_frame(incidents: pd.DataFrame) -> pd.DataFrame:
    frame = incidents.copy()
    frame = frame.rename(
        columns={
            "industry": "org_type",
            "organization_code": "enterprise_code",
        }
    )
    return frame


def _merge_notebook_frames(incidents: pd.DataFrame, threatlist: pd.DataFrame) -> pd.DataFrame:
    incidents = incidents.copy()
    threatlist = threatlist.copy()

    for col in ["org_type", "region"]:
        incidents[col] = incidents[col].astype(str).str.strip()

    for col in ["host_count", "threat_code", "success"]:
        incidents[col] = pd.to_numeric(incidents[col], errors="coerce")

    incidents["enterprise_code"] = incidents["enterprise_code"].astype(str).str.strip()
    incidents["regional_time"] = pd.to_datetime(incidents["regional_time"], errors="coerce", dayfirst=True)

    incidents = incidents.dropna(
        subset=["org_type", "enterprise_code", "host_count", "threat_code", "success", "region", "regional_time"]
    ).copy()
    incidents["success"] = incidents["success"].astype(int)
    incidents = incidents[incidents["success"].isin([0, 1])].copy()

    for col in ["threat_name", "threat_source", "impact_object"]:
        if col in threatlist.columns:
            threatlist[col] = threatlist[col].astype(str).str.strip()

    for col in ["threat_code", "confidentiality_violation", "integrity_violation", "availability_violation"]:
        if col in threatlist.columns:
            threatlist[col] = pd.to_numeric(threatlist[col], errors="coerce")

    threatlist = threatlist.dropna(subset=["threat_code"]).drop_duplicates(subset=["threat_code"]).copy()

    df = incidents.merge(threatlist, on="threat_code", how="left")

    for col in ["threat_name", "threat_source", "impact_object"]:
        if col in df.columns:
            df[col] = df[col].fillna("Неизвестно")

    for col in ["confidentiality_violation", "integrity_violation", "availability_violation"]:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)

    df = df.sort_values("regional_time").reset_index(drop=True)
    return df


def build_merged_incidents_df(incidents: pd.DataFrame, registry: pd.DataFrame) -> pd.DataFrame:
    """Convert repository/DB frames into the notebook-compatible merged training frame."""
    if incidents.empty:
        return incidents.iloc[0:0].copy()

    return _merge_notebook_frames(_normalize_incidents_frame(incidents), _normalize_registry_frame(registry))

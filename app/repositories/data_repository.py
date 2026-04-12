from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

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
FSTEC_PATH = _locate_data_file('Файл с сайта ФСТЭК.xlsx')


class DataRepository:
    def __init__(self, incidents_path: Path = INCIDENTS_PATH, fstec_path: Path = FSTEC_PATH):
        self.incidents_path = incidents_path
        self.fstec_path = fstec_path

    @lru_cache(maxsize=1)
    def load_incidents(self) -> pd.DataFrame:
        frame = pd.read_excel(self.incidents_path)
        frame = frame.rename(
            columns={
                'Тип предприятия': 'industry',
                'Код предприятия': 'organization_code',
                'Количество хостов': 'host_count',
                'Код реализованной угрозы': 'threat_code',
                'Успех': 'success',
                'Регион размещения предприятия': 'region',
                'Дата инцидента': 'incident_date',
                'Региональное время': 'regional_time',
            }
        )
        frame['incident_date'] = pd.to_datetime(frame['incident_date'], errors='coerce', dayfirst=True)
        frame['regional_time'] = pd.to_datetime(frame['regional_time'], errors='coerce', dayfirst=True)
        frame['hour'] = frame['regional_time'].dt.hour.fillna(0).astype(int)
        frame['month'] = frame['incident_date'].dt.month.fillna(1).astype(int)
        frame['season'] = frame['month'].map(
            {
                12: 'winter', 1: 'winter', 2: 'winter',
                3: 'spring', 4: 'spring', 5: 'spring',
                6: 'summer', 7: 'summer', 8: 'summer',
                9: 'autumn', 10: 'autumn', 11: 'autumn',
            }
        )
        frame['time_of_day'] = frame['hour'].map(self._time_of_day)
        return frame

    @lru_cache(maxsize=1)
    def load_fstec_registry(self) -> pd.DataFrame:
        frame = pd.read_excel(self.fstec_path)
        frame.columns = frame.iloc[0].tolist()
        frame = frame.iloc[1:].reset_index(drop=True)
        frame = frame.rename(
            columns={
                'Идентификатор УБИ': 'threat_code',
                'Наименование УБИ': 'name',
                'Описание': 'description',
                'Объект воздействия': 'object_of_impact',
                'Статус угрозы': 'status',
            }
        )
        frame['threat_code'] = pd.to_numeric(frame['threat_code'], errors='coerce').astype('Int64')
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
    return DataRepository()

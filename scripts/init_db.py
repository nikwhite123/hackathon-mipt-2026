from __future__ import annotations

import pandas as pd
from sqlalchemy import create_engine, text

from app.db.base import Base
from app.models import Organization, User  # noqa: F401

DATABASE_URL = 'postgresql+psycopg2://app_user:app_password@db:5432/rostelecom_db'
INCIDENTS_PATH = 'data/incidents_2000.xlsx'


def main() -> None:
    engine = create_engine(DATABASE_URL, future=True)
    Base.metadata.create_all(bind=engine)

    incidents = pd.read_excel(INCIDENTS_PATH)
    organizations = (
        incidents[['Код предприятия']]
        .dropna()
        .astype({'Код предприятия': int})
        .drop_duplicates()
        .sort_values('Код предприятия')
    )

    with engine.begin() as connection:
        existing = connection.execute(text('SELECT COUNT(*) FROM organizations')).scalar_one()
        if existing == 0:
            for code in organizations['Код предприятия'].tolist():
                connection.execute(
                    text('INSERT INTO organizations (name, code) VALUES (:name, :code)'),
                    {'name': f'Организация {code}', 'code': str(code)},
                )


if __name__ == '__main__':
    main()

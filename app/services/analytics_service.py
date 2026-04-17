from __future__ import annotations

from app.repositories.data_repository import DataRepository
from app.schemas import ThreatStats


class AnalyticsService:
    def __init__(self, repository: DataRepository):
        self.repository = repository

    def build_stats(self, organization_code: str | None = None) -> ThreatStats:
        incidents = self.repository.load_incidents_by_organization_code(organization_code)
        registry = self.repository.load_fstec_registry()[['threat_code', 'name', 'description', 'object_of_impact']]
        dataset = incidents.merge(registry, on='threat_code', how='left')
        dataset['attack_method'] = dataset.apply(self._detect_attack_method, axis=1)
        dataset['target_object'] = dataset.apply(self._detect_target_object, axis=1)
        dataset['risk_level'] = dataset.apply(self._detect_risk_level, axis=1)

        return ThreatStats(
            total_incidents=len(dataset),
            top_attack_method=dataset['attack_method'].value_counts().idxmax() if not dataset.empty else 'malware',
            top_target_object=dataset['target_object'].value_counts().idxmax() if not dataset.empty else 'workstation',
            risk_distribution=dataset['risk_level'].value_counts().sort_index().to_dict(),
            incidents_by_season=dataset['season'].value_counts().sort_index().to_dict(),
            incidents_by_time_of_day=dataset['time_of_day'].value_counts().sort_index().to_dict(),
            incidents_by_hour=dataset.groupby('hour').size().sort_index().astype(int).to_dict(),
            incidents_by_region=dataset['region'].value_counts().head(15).astype(int).to_dict(),
            incidents_by_target_object=dataset['target_object'].value_counts().sort_index().astype(int).to_dict(),
        )

    @staticmethod
    def _normalize_text(*parts: object) -> str:
        return ' '.join(str(part) for part in parts if part and str(part) != 'nan').lower()

    def _detect_attack_method(self, row) -> str:
        text = self._normalize_text(row.get('name'), row.get('description'), row.get('object_of_impact'))
        rules = [
            ('ransomware', ['шифров', 'вымогат', 'ransomware']),
            ('sql_injection', ['sql', 'инъек', 'входных данных', 'запрос']),
            ('credential_stuffing', ['учётн', 'учетн', 'credential', 'доступа к сетевым сервисам']),
            ('brute_force', ['подбор', 'парол', 'аутентификац', 'авторизац', 'логин']),
            ('phishing', ['фиш', 'почтов', 'почт', 'спам']),
            ('malware', ['вредонос', 'троян', 'worm', 'черв', 'код']),
        ]
        for method, tokens in rules:
            if any(token in text for token in tokens):
                return method
        return 'malware'

    def _detect_target_object(self, row) -> str:
        text = self._normalize_text(row.get('object_of_impact'), row.get('name'), row.get('description'))
        rules = [
            ('vpn_gateway', ['vpn', 'удален', 'сетевым сервисам']),
            ('mail_gateway', ['почт', 'mail', 'спам', 'фиш']),
            ('crm', ['crm', 'учётные данные пользователя', 'учетные данные пользователя']),
            ('db_server', ['баз', 'субд', 'sql']),
            ('web_portal', ['веб', 'web', 'сайт', 'портал', 'браузер']),
            ('file_server', ['файл', 'хранил', 'общие папки']),
            ('workstation', ['bios', 'uefi', 'компьютер', 'рабоч', 'микропрограмм']),
        ]
        for target, tokens in rules:
            if any(token in text for token in tokens):
                return target
        return 'workstation'

    def _detect_risk_level(self, row) -> str:
        success = int(row.get('success', 0))
        host_count = int(row.get('host_count', 0))
        method = row.get('attack_method') or self._detect_attack_method(row)
        score = success * 2
        if host_count >= 1000:
            score += 1
        if method in {'ransomware', 'credential_stuffing'}:
            score += 1
        if score >= 4:
            return 'critical'
        if score >= 3:
            return 'high'
        if score >= 2:
            return 'medium'
        return 'low'

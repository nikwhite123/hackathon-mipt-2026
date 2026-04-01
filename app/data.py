from __future__ import annotations

from app.schemas import AttackMethod, TargetObject, ThreatSeverity

THREATS = [
    {
        "threat_id": "TH-001",
        "name": "Компрометация CRM через фишинговую рассылку",
        "description": "Получение доступа к CRM через кражу учетных данных сотрудников.",
        "category": "credential_access",
        "severity": ThreatSeverity.high,
        "likely_targets": [TargetObject.crm, TargetObject.mail_gateway],
        "common_methods": [AttackMethod.phishing, AttackMethod.credential_stuffing],
    },
    {
        "threat_id": "TH-002",
        "name": "Шифровальщик на файловом сервере",
        "description": "Распространение ransomware внутри сегмента с общими папками.",
        "category": "impact",
        "severity": ThreatSeverity.critical,
        "likely_targets": [TargetObject.file_server, TargetObject.workstation],
        "common_methods": [AttackMethod.ransomware, AttackMethod.malware],
    },
    {
        "threat_id": "TH-003",
        "name": "Атака на VPN-шлюз через подбор пароля",
        "description": "Попытка доступа через слабые пароли и отсутствие MFA.",
        "category": "initial_access",
        "severity": ThreatSeverity.high,
        "likely_targets": [TargetObject.vpn_gateway],
        "common_methods": [AttackMethod.brute_force, AttackMethod.credential_stuffing],
    },
    {
        "threat_id": "TH-004",
        "name": "SQL-инъекция в веб-портал",
        "description": "Эксплуатация входных форм без корректной валидации.",
        "category": "application_attack",
        "severity": ThreatSeverity.medium,
        "likely_targets": [TargetObject.web_portal, TargetObject.db_server],
        "common_methods": [AttackMethod.sql_injection],
    },
    {
        "threat_id": "TH-005",
        "name": "Вредоносное ПО на рабочей станции",
        "description": "Загрузка трояна пользователем с последующим lateral movement.",
        "category": "execution",
        "severity": ThreatSeverity.medium,
        "likely_targets": [TargetObject.workstation, TargetObject.file_server],
        "common_methods": [AttackMethod.malware, AttackMethod.phishing],
    },
]

RECOMMENDATIONS = {
    AttackMethod.phishing: [
        {
            "code": "PR-001",
            "title": "Включить защищенную почтовую фильтрацию",
            "description": "Активировать антифишинговые правила и sandbox-анализ вложений.",
            "priority": 1,
        },
        {
            "code": "PR-002",
            "title": "Провести принудительную смену паролей",
            "description": "Сменить пароли критичных пользователей и проверить повторное использование учетных данных.",
            "priority": 2,
        },
        {
            "code": "PR-003",
            "title": "Запустить обучение сотрудников",
            "description": "Провести короткую кампанию по распознаванию фишинговых писем.",
            "priority": 3,
        },
    ],
    AttackMethod.brute_force: [
        {
            "code": "PR-004",
            "title": "Включить MFA",
            "description": "Обязать MFA для всех внешних точек входа и администраторов.",
            "priority": 1,
        },
        {
            "code": "PR-005",
            "title": "Ограничить попытки входа",
            "description": "Включить rate limiting, блокировки и CAPTCHA на публичных формах входа.",
            "priority": 2,
        },
    ],
    AttackMethod.ransomware: [
        {
            "code": "PR-006",
            "title": "Проверить резервные копии",
            "description": "Убедиться, что резервные копии изолированы и восстановление проходит успешно.",
            "priority": 1,
        },
        {
            "code": "PR-007",
            "title": "Ограничить lateral movement",
            "description": "Сегментировать сеть и ограничить доступ между рабочими станциями и серверами.",
            "priority": 2,
        },
    ],
    AttackMethod.sql_injection: [
        {
            "code": "PR-008",
            "title": "Включить WAF-правила",
            "description": "Активировать правила защиты от SQL-инъекций для внешнего веб-контура.",
            "priority": 1,
        },
        {
            "code": "PR-009",
            "title": "Проверить параметризованные запросы",
            "description": "Исключить динамическую конкатенацию SQL-строк в коде.",
            "priority": 2,
        },
    ],
    AttackMethod.malware: [
        {
            "code": "PR-010",
            "title": "Обновить EDR/AV-политики",
            "description": "Усилить правила детектирования и запретить запуск неподписанных файлов.",
            "priority": 1,
        },
        {
            "code": "PR-011",
            "title": "Ограничить права локальных пользователей",
            "description": "Убрать локальные административные права у офисных рабочих станций.",
            "priority": 2,
        },
    ],
    AttackMethod.credential_stuffing: [
        {
            "code": "PR-012",
            "title": "Проверить утечки учетных данных",
            "description": "Сопоставить логины сотрудников с известными утечками и инициировать смену паролей.",
            "priority": 1,
        },
        {
            "code": "PR-013",
            "title": "Включить контроль аномального входа",
            "description": "Настроить алерты на массовые неуспешные логины и геоаномалии.",
            "priority": 2,
        },
    ],
}

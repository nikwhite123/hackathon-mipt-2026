#!/usr/bin/env node

const fs = require('fs');
const os = require('os');
const path = require('path');
const { Command } = require('commander');
const chalk = require('chalk');
const axios = require('axios');
const Table = require('cli-table3');

const DEFAULT_BASE_URL = process.env.RT_API_BASE_URL || 'http://127.0.0.1:8000';
const DEFAULT_CONFIG_PATH = path.join(os.homedir(), '.rt-threat-analytics-cli.json');
const program = new Command();

program
    .name('rt')
    .description('CLI-клиент для актуальных ручек RT Threat Analytics API')
    .version('2.0.0')
    .option('-u, --base-url <url>', 'Базовый URL API', DEFAULT_BASE_URL)
    .option('-t, --token <token>', 'Bearer token для защищённых ручек')
    .option('--json', 'Печатать сырой JSON-ответ вместо форматированного вывода');

function getBaseUrl() {
    const options = program.opts();
    return (options.baseUrl || DEFAULT_BASE_URL).replace(/\/+$/, '');
}

function getApi() {
    const token = getToken();
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }
    return axios.create({
        baseURL: getBaseUrl(),
        timeout: 30000,
        headers,
    });
}

function isJsonOutput() {
    return Boolean(program.opts().json);
}

function printJson(data) {
    console.log(JSON.stringify(data, null, 2));
}

function loadCliConfig() {
    try {
        if (!fs.existsSync(DEFAULT_CONFIG_PATH)) {
            return {};
        }
        return JSON.parse(fs.readFileSync(DEFAULT_CONFIG_PATH, 'utf-8'));
    } catch {
        return {};
    }
}

function saveCliConfig(nextConfig) {
    fs.writeFileSync(DEFAULT_CONFIG_PATH, JSON.stringify(nextConfig, null, 2), 'utf-8');
}

function clearCliConfigToken() {
    const config = loadCliConfig();
    delete config.token;
    saveCliConfig(config);
}

function persistCliToken(token) {
    const config = loadCliConfig();
    config.token = token;
    saveCliConfig(config);
}

function getToken() {
    const options = program.opts();
    if (options.token) {
        return options.token;
    }
    if (process.env.RT_API_TOKEN) {
        return process.env.RT_API_TOKEN;
    }
    return loadCliConfig().token || null;
}

function printSection(title) {
    console.log('\n' + chalk.bold.hex('#7733FF')(title));
}

function severityColor(severity) {
    if (severity === 'critical') return chalk.red.bold;
    if (severity === 'high') return chalk.red;
    if (severity === 'medium') return chalk.yellow;
    if (severity === 'low') return chalk.green;
    return chalk.white;
}

function formatPercent(value) {
    return `${(Number(value) * 100).toFixed(0)}%`;
}

function normalizeBooleanOption(value, fallback = true) {
    if (typeof value === 'boolean') {
        return value;
    }
    return fallback;
}

function defaultSeason() {
    const month = new Date().getMonth() + 1;
    if ([12, 1, 2].includes(month)) return 'winter';
    if ([3, 4, 5].includes(month)) return 'spring';
    if ([6, 7, 8].includes(month)) return 'summer';
    return 'autumn';
}

function defaultDayOfWeek() {
    const jsDay = new Date().getDay();
    return jsDay === 0 ? 7 : jsDay;
}

function defaultHour() {
    return new Date().getHours();
}

function readJsonFile(filePath) {
    const resolved = path.resolve(process.cwd(), filePath);
    const raw = fs.readFileSync(resolved, 'utf-8');
    return JSON.parse(raw);
}

function buildPredictPayload(organizationId, options) {
    if (options.payloadFile) {
        return readJsonFile(options.payloadFile);
    }
    if (!organizationId) {
        throw new Error('Нужен <organizationId> или --payload-file <file>.');
    }
    return {
        organization_id: organizationId,
        region: options.region || 'Moscow',
        industry: options.industry || 'telecom',
        season: options.season || defaultSeason(),
        day_of_week: Number(options.dayOfWeek ?? defaultDayOfWeek()),
        hour: Number(options.hour ?? defaultHour()),
        asset_type: options.assetType || 'vpn_gateway',
        has_external_access: normalizeBooleanOption(options.externalAccess, true),
        privileged_accounts_count: Number(options.privilegedAccountsCount ?? 12),
        known_vulnerabilities_count: Number(options.knownVulnerabilitiesCount ?? 3),
        prefer_ml: normalizeBooleanOption(options.preferMl, false),
    };
}

function printRationale(lines) {
    if (!Array.isArray(lines) || lines.length === 0) {
        return;
    }
    printSection('Обоснование');
    for (const line of lines) {
        console.log(chalk.gray(`• ${line}`));
    }
}

function printRecommendations(recommendations) {
    if (!Array.isArray(recommendations) || recommendations.length === 0) {
        return;
    }
    printSection('Рекомендации');
    for (const recommendation of recommendations) {
        console.log(
            `${chalk.green('✔')} ${chalk.white(recommendation.title)} ${chalk.gray(`(${recommendation.code}, p${recommendation.priority})`)}`
        );
    }
}

function printValidationErrors(errors) {
    if (!Array.isArray(errors) || errors.length === 0) {
        return;
    }
    printSection('Validation errors');
    for (const error of errors) {
        const location = Array.isArray(error.loc) ? error.loc.join('.') : String(error.loc);
        console.log(`${chalk.red('•')} ${location}: ${error.msg}`);
    }
}

function handleApiError(error, fallbackMessage) {
    if (error.response) {
        const detail = error.response.data?.detail || fallbackMessage;
        console.error(chalk.red(`✘ ${detail}`));
        printValidationErrors(error.response.data?.errors);
        if (error.response.status === 401) {
            console.error(chalk.yellow('Нужна авторизация. Выполните `rt login <email> <password>` или передайте `--token`.'));
        }
        return;
    }
    if (error.request) {
        console.error(chalk.red(`✘ Backend недоступен: ${getBaseUrl()}`));
        console.error(chalk.yellow('Запустите API: `uvicorn app.main:app --reload --port 8000`'));
        return;
    }
    console.error(chalk.red(`✘ ${fallbackMessage}`));
    console.error(chalk.gray(String(error.message || error)));
}

function addPredictionOptions(command) {
    return command
        .option('--payload-file <file>', 'Путь к JSON-файлу в формате PredictRequest')
        .option('--region <region>', 'Регион организации', 'Moscow')
        .option('--industry <industry>', 'Отрасль', 'telecom')
        .option('--season <season>', 'Сезон: winter|spring|summer|autumn', defaultSeason())
        .option('--day-of-week <number>', 'День недели: 1..7', String(defaultDayOfWeek()))
        .option('--hour <number>', 'Час: 0..23', String(defaultHour()))
        .option('--asset-type <assetType>', 'Тип актива', 'vpn_gateway')
        .option('--prefer-ml', 'Предпочесть ML-ветку там, где она доступна')
        .option('--no-external-access', 'Отключить внешний доступ')
        .option('--privileged-accounts-count <number>', 'Количество привилегированных учеток', '12')
        .option('--known-vulnerabilities-count <number>', 'Количество известных уязвимостей', '3');
}

async function runPrediction(endpoint, organizationId, options, printer) {
    try {
        const payload = buildPredictPayload(organizationId, options);
        const response = await getApi().post(endpoint, payload);
        if (isJsonOutput()) {
            printJson(response.data);
            return;
        }
        printer(response.data, payload);
    } catch (error) {
        handleApiError(error, `Ошибка при вызове ${endpoint}`);
        process.exitCode = 1;
    }
}

program
    .command('welcome')
    .description('Показать список доступных команд для актуальных ручек API')
    .action(() => {
        const logoText = `
██████╗ ████████╗    ██╗███╗   ██╗███████╗██████╗  █████╗
██╔══██╗╚══██╔══╝    ██║████╗  ██║██╔════╝██╔══██╗██╔══██╗
██████╔╝   ██║       ██║██╔██╗ ██║█████╗  ██████╔╝███████║
██╔══██╗   ██║       ██║██║╚██╗██║██╔══╝  ██╔══██╗██╔══██║
██║  ██║   ██║       ██║██║ ╚████║██║     ██║  ██║██║  ██║
╚═╝  ╚═╝   ╚═╝       ╚═╝╚═╝  ╚═══╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝
`;

        console.log(chalk.hex('#7733FF').bold(logoText));
        const table = new Table({
            head: [chalk.bold.hex('#FF502F')('Команда'), chalk.bold.hex('#FF502F')('Что делает')],
            colWidths: [28, 58],
            wordWrap: true,
        });

        table.push(
            ['status', 'Проверяет `GET /health`'],
            ['ready', 'Проверяет `GET /ready`'],
            ['onboarding', 'Показывает пошаговый старт с CLI и organization_code'],
            ['threats', 'Показывает `GET /threats` с фильтрами severity/category'],
            ['stats', 'Печатает сводку по `GET /stats`'],
            ['stats-facets', 'Показывает `GET /stats/facets`'],
            ['predict', 'Вызывает `POST /predict`'],
            ['predict-time', 'Вызывает `POST /predict/time`'],
            ['predict-target', 'Вызывает `POST /predict/target`'],
            ['predict-method', 'Вызывает `POST /predict/method`'],
            ['predict-recommendations', 'Вызывает `POST /predict/recommendations`'],
            ['login', 'Вызывает `POST /auth/login` и сохраняет токен'],
            ['register', 'Вызывает `POST /auth/register`'],
            ['me', 'Вызывает `GET /auth/me`'],
            ['logout', 'Удаляет локально сохранённый токен'],
            ['org-lookup', 'Вызывает `GET /auth/organization/by-code`'],
            ['org-codes', 'Показывает коды организаций из `GET /stats/facets` после логина'],
            ['org-settings-get', 'Вызывает `GET /org/settings`'],
            ['org-settings-set', 'Вызывает `POST /org/settings`'],
            ['vuln-map', 'Вызывает `POST /vulnerabilities/map` из JSON-файла'],
            ['openapi', 'Показывает сведения по `/openapi.json`'],
        );

        console.log(table.toString());
        console.log(chalk.gray(`\nBase URL: ${getBaseUrl()}`));
        console.log(chalk.gray('Используйте `--help` у команды для списка опций.'));
    });

program
    .command('status')
    .description('Проверить доступность `GET /health`')
    .action(async () => {
        try {
            const response = await getApi().get('/health');
            console.log(chalk.green('✔ Backend доступен'));
            console.log(`${chalk.white('URL:')} ${getBaseUrl()}`);
            console.log(`${chalk.white('Status:')} ${chalk.bold(response.data.status)}`);
        } catch (error) {
            handleApiError(error, 'Ошибка проверки health');
            process.exitCode = 1;
        }
    });

program
    .command('ready')
    .description('Проверить готовность `GET /ready`')
    .action(async () => {
        try {
            const response = await getApi().get('/ready');
            if (isJsonOutput()) {
                printJson(response.data);
                return;
            }
            console.log(chalk.green('✔ Backend ready'));
            console.log(`${chalk.white('URL:')} ${getBaseUrl()}`);
            console.log(`${chalk.white('Status:')} ${chalk.bold(response.data.status)}`);
            console.log(`${chalk.white('Database:')} ${response.data.checks?.database?.ok ? chalk.green('ok') : chalk.red('failed')}`);
        } catch (error) {
            handleApiError(error, 'Ошибка проверки ready');
            process.exitCode = 1;
        }
    });

program
    .command('onboarding')
    .description('Показать пошаговый onboarding для глобального `rt` и поиска organization_code')
    .action(() => {
        const lines = [
            '1. Установите CLI глобально:',
            '   cd cli && npm install && npm link',
            '',
            '2. Проверьте backend:',
            '   rt status',
            '   rt ready',
            '',
            '3. Если organization_code уже известен, проверьте его:',
            '   rt org-lookup <organization_code>',
            '',
            '4. Если organization_code неизвестен:',
            '   - попросите код у команды / возьмите из сидов;',
            '   - после логина можно посмотреть свой контекст через `rt org-codes`.',
            '',
            '5. Зарегистрируйтесь и сохраните токен:',
            '   rt register Ivan Petrov ivan@example.com Secret12345 <organization_code>',
            '   rt login ivan@example.com Secret12345',
            '   rt me',
            '',
            '6. Проверьте прогнозы:',
            '   rt predict <organization_code> --region Moscow --industry telecom --asset-type vpn_gateway --prefer-ml',
            '   rt predict --payload-file ./examples/predict.sample.json',
            '',
            '7. Для маппинга уязвимостей:',
            '   rt vuln-map ./examples/vulnerabilities.sample.json',
            '',
            `Config file for saved token: ${DEFAULT_CONFIG_PATH}`,
        ];

        if (isJsonOutput()) {
            printJson({ steps: lines });
            return;
        }

        printSection('CLI onboarding');
        lines.forEach((line) => console.log(line));
    });

program
    .command('threats')
    .description('Показать список угроз из `GET /threats`')
    .option('--severity <severity>', 'Фильтр severity: low|medium|high|critical')
    .option('--category <category>', 'Фильтр по категории')
    .option('--limit <number>', 'Показать только первые N записей')
    .action(async (options) => {
        try {
            const response = await getApi().get('/threats', {
                params: {
                    severity: options.severity,
                    category: options.category,
                },
            });
            const limit = options.limit ? Number(options.limit) : undefined;
            const items = limit ? response.data.items.slice(0, limit) : response.data.items;
            const table = new Table({
                head: ['ID', 'Название', 'Категория', 'Severity', 'Targets'],
                colWidths: [10, 34, 20, 12, 28],
                wordWrap: true,
            });

            items.forEach((item) => {
                table.push([
                    item.threat_id,
                    item.name,
                    item.category,
                    severityColor(item.severity)(item.severity.toUpperCase()),
                    item.likely_targets.join(', '),
                ]);
            });

            if (isJsonOutput()) {
                printJson(response.data);
                return;
            }

            console.log(table.toString());
            console.log(chalk.gray(`Всего записей: ${response.data.total}`));
        } catch (error) {
            handleApiError(error, 'Ошибка получения списка угроз');
            process.exitCode = 1;
        }
    });

program
    .command('stats')
    .description('Показать сводку из `GET /stats`')
    .action(async () => {
        try {
            const response = await getApi().get('/stats');
            const stats = response.data;

            if (isJsonOutput()) {
                printJson(stats);
                return;
            }

            printSection('RT Threat Analytics Summary');
            console.log(`${chalk.white('Всего инцидентов:')} ${chalk.bold(stats.total_incidents)}`);
            console.log(`${chalk.white('Топ метод атаки:')} ${chalk.red(stats.top_attack_method)}`);
            console.log(`${chalk.white('Основная цель:')} ${chalk.cyan(stats.top_target_object)}`);

            const risk = stats.risk_distribution || {};
            printSection('Risk distribution');
            console.log(`${chalk.red('critical:')} ${risk.critical ?? 0}`);
            console.log(`${chalk.red('high:')}     ${risk.high ?? 0}`);
            console.log(`${chalk.yellow('medium:')}   ${risk.medium ?? 0}`);
            console.log(`${chalk.green('low:')}      ${risk.low ?? 0}`);

            printSection('Top regions');
            Object.entries(stats.incidents_by_region || {})
                .slice(0, 10)
                .forEach(([region, count]) => console.log(`• ${region}: ${count}`));

            printSection('Top target objects');
            Object.entries(stats.incidents_by_target_object || {})
                .sort(([, a], [, b]) => b - a)
                .slice(0, 5)
                .forEach(([target, count]) => console.log(`• ${target}: ${count}`));
        } catch (error) {
            handleApiError(error, 'Ошибка получения статистики');
            process.exitCode = 1;
        }
    });

program
    .command('stats-facets')
    .description('Показать значения фильтров из `GET /stats/facets`')
    .action(async () => {
        try {
            const response = await getApi().get('/stats/facets');
            const data = response.data;
            if (isJsonOutput()) {
                printJson(data);
                return;
            }

            printSection('Stats facets');
            console.log(chalk.white('Regions:'));
            (data.regions || []).forEach((item) => console.log(`• ${item}`));
            console.log(chalk.white('\nIndustries:'));
            (data.industries || []).forEach((item) => console.log(`• ${item}`));
        } catch (error) {
            handleApiError(error, 'Ошибка получения stats facets');
            process.exitCode = 1;
        }
    });

program
    .command('login <email> <password>')
    .description('Логин через `POST /auth/login` с сохранением токена')
    .option('--no-save-token', 'Не сохранять токен локально')
    .action(async (email, password, options) => {
        try {
            const response = await getApi().post('/auth/login', { email, password });
            const data = response.data;
            if (options.saveToken) {
                persistCliToken(data.access_token);
            }
            if (isJsonOutput()) {
                printJson(data);
                return;
            }

            printSection('Login successful');
            console.log(`${chalk.white('Email:')} ${data.user.email}`);
            console.log(`${chalk.white('Organization:')} ${data.user.organization_name} ${chalk.gray(`(${data.user.organization_code ?? 'no-code'})`)}`);
            console.log(`${chalk.white('Token saved:')} ${options.saveToken ? chalk.green('yes') : chalk.yellow('no')}`);
        } catch (error) {
            handleApiError(error, 'Ошибка логина');
            process.exitCode = 1;
        }
    });

program
    .command('register <firstName> <lastName> <email> <password> <organizationCode>')
    .description('Регистрация через `POST /auth/register`')
    .action(async (firstName, lastName, email, password, organizationCode) => {
        try {
            const response = await getApi().post('/auth/register', {
                first_name: firstName,
                last_name: lastName,
                email,
                password,
                organization_code: organizationCode,
            });
            if (isJsonOutput()) {
                printJson(response.data);
                return;
            }

            printSection('Registration successful');
            console.log(`${chalk.white('User ID:')} ${response.data.id}`);
            console.log(`${chalk.white('Email:')} ${response.data.email}`);
            console.log(`${chalk.white('Organization:')} ${response.data.organization_name}`);
        } catch (error) {
            handleApiError(error, 'Ошибка регистрации');
            process.exitCode = 1;
        }
    });

program
    .command('me')
    .description('Текущий пользователь через `GET /auth/me`')
    .action(async () => {
        try {
            const response = await getApi().get('/auth/me');
            if (isJsonOutput()) {
                printJson(response.data);
                return;
            }
            const me = response.data;
            printSection('Current user');
            console.log(`${chalk.white('Name:')} ${me.first_name} ${me.last_name}`);
            console.log(`${chalk.white('Email:')} ${me.email}`);
            console.log(`${chalk.white('Organization:')} ${me.organization_name} ${chalk.gray(`(${me.organization_code ?? 'no-code'})`)}`);
        } catch (error) {
            handleApiError(error, 'Ошибка получения текущего пользователя');
            process.exitCode = 1;
        }
    });

program
    .command('logout')
    .description('Удалить локально сохранённый токен')
    .action(() => {
        clearCliConfigToken();
        console.log(chalk.green('✔ Локальный токен удалён'));
    });

program
    .command('org-lookup <organizationCode>')
    .description('Поиск организации через `GET /auth/organization/by-code`')
    .action(async (organizationCode) => {
        try {
            const response = await getApi().get('/auth/organization/by-code', {
                params: { code: organizationCode },
            });
            if (isJsonOutput()) {
                printJson(response.data);
                return;
            }
            const organization = response.data;
            printSection('Organization');
            console.log(`${chalk.white('ID:')} ${organization.id}`);
            console.log(`${chalk.white('Name:')} ${organization.name}`);
            console.log(`${chalk.white('Code:')} ${organization.code}`);
        } catch (error) {
            handleApiError(error, 'Ошибка поиска организации');
            process.exitCode = 1;
        }
    });

program
    .command('org-codes')
    .description('Показать доступные коды организаций из JWT-контекста через `GET /auth/me` и `GET /stats/facets`')
    .action(async () => {
        try {
            const [meResponse, facetsResponse] = await Promise.all([
                getApi().get('/auth/me'),
                getApi().get('/stats/facets'),
            ]);
            const me = meResponse.data;
            const facets = facetsResponse.data;
            const payload = {
                organization_code: me.organization_code,
                organization_name: me.organization_name,
                regions: facets.regions || [],
                industries: facets.industries || [],
            };
            if (isJsonOutput()) {
                printJson(payload);
                return;
            }

            printSection('Organization context');
            console.log(`${chalk.white('Code:')} ${me.organization_code ?? 'n/a'}`);
            console.log(`${chalk.white('Name:')} ${me.organization_name}`);
            console.log(`${chalk.white('Regions:')} ${(facets.regions || []).join(', ') || 'none'}`);
            console.log(`${chalk.white('Industries:')} ${(facets.industries || []).join(', ') || 'none'}`);
        } catch (error) {
            handleApiError(error, 'Ошибка получения organization context');
            process.exitCode = 1;
        }
    });

program
    .command('org-settings-get')
    .description('Получить настройки организации через `GET /org/settings`')
    .action(async () => {
        try {
            const response = await getApi().get('/org/settings');
            if (isJsonOutput()) {
                printJson(response.data);
                return;
            }
            if (!response.data) {
                console.log(chalk.yellow('Настройки организации ещё не заданы.'));
                return;
            }
            const data = response.data;
            printSection('Organization settings');
            console.log(`${chalk.white('Region:')} ${data.region}`);
            console.log(`${chalk.white('Industry:')} ${data.industry}`);
            console.log(`${chalk.white('Host count:')} ${data.host_count}`);
            console.log(`${chalk.white('Technologies:')} ${(data.technologies || []).join(', ') || 'none'}`);
        } catch (error) {
            handleApiError(error, 'Ошибка получения настроек организации');
            process.exitCode = 1;
        }
    });

program
    .command('org-settings-set')
    .description('Сохранить настройки организации через `POST /org/settings`')
    .requiredOption('--region <region>', 'Регион')
    .requiredOption('--industry <industry>', 'Отрасль')
    .requiredOption('--host-count <number>', 'Количество хостов')
    .option('--technologies <items>', 'Список технологий через запятую')
    .action(async (options) => {
        try {
            const payload = {
                region: options.region,
                industry: options.industry,
                host_count: Number(options.hostCount),
                technologies: options.technologies
                    ? options.technologies.split(',').map((item) => item.trim()).filter(Boolean)
                    : [],
            };
            const response = await getApi().post('/org/settings', payload);
            if (isJsonOutput()) {
                printJson(response.data);
                return;
            }
            printSection('Organization settings saved');
            console.log(`${chalk.white('Region:')} ${response.data.region}`);
            console.log(`${chalk.white('Industry:')} ${response.data.industry}`);
            console.log(`${chalk.white('Host count:')} ${response.data.host_count}`);
        } catch (error) {
            handleApiError(error, 'Ошибка сохранения настроек организации');
            process.exitCode = 1;
        }
    });

program
    .command('openapi')
    .description('Показать информацию по `GET /openapi.json`')
    .action(async () => {
        try {
            const response = await getApi().get('/openapi.json');
            const schema = response.data;
            if (isJsonOutput()) {
                printJson(schema);
                return;
            }

            const paths = Object.keys(schema.paths || {});
            printSection('OpenAPI');
            console.log(`${chalk.white('Title:')} ${schema.info?.title ?? 'n/a'}`);
            console.log(`${chalk.white('Version:')} ${schema.info?.version ?? 'n/a'}`);
            console.log(`${chalk.white('Paths:')} ${paths.length}`);
            paths.sort().forEach((route) => console.log(`• ${route}`));
        } catch (error) {
            handleApiError(error, 'Ошибка получения openapi схемы');
            process.exitCode = 1;
        }
    });

addPredictionOptions(
    program
        .command('predict [organizationId]')
        .description('Полный прогноз через `POST /predict`')
).action(async (organizationId, options) => {
    await runPrediction('/predict', organizationId, options, (data) => {
        printSection('Прогноз');
        console.log(`${chalk.white('Risk score:')} ${chalk.red.bold(formatPercent(data.risk_score))}`);
        console.log(`${chalk.white('Метод:')} ${chalk.cyan(data.predicted_attack_method)}`);
        console.log(`${chalk.white('Цель:')} ${chalk.cyan(data.predicted_target_object)}`);
        console.log(`${chalk.white('Окно атаки:')} ${chalk.yellow(data.predicted_attack_time_window)}`);
        console.log(`${chalk.white('Confidence:')} ${chalk.bold(formatPercent(data.confidence))}`);
        printRationale(data.rationale);
        printRecommendations(data.recommendations);
    });
});

addPredictionOptions(
    program
        .command('predict-time [organizationId]')
        .description('Прогноз временного окна через `POST /predict/time`')
).action(async (organizationId, options) => {
    await runPrediction('/predict/time', organizationId, options, (data) => {
        printSection('Time prediction');
        console.log(`${chalk.white('Окно атаки:')} ${chalk.yellow(data.predicted_attack_time_window)}`);
        console.log(`${chalk.white('Confidence:')} ${chalk.bold(formatPercent(data.confidence))}`);
        printRationale(data.rationale);
    });
});

addPredictionOptions(
    program
        .command('predict-target [organizationId]')
        .description('Прогноз объекта атаки через `POST /predict/target`')
).action(async (organizationId, options) => {
    await runPrediction('/predict/target', organizationId, options, (data) => {
        printSection('Target prediction');
        console.log(`${chalk.white('Цель:')} ${chalk.cyan(data.predicted_target_object)}`);
        console.log(`${chalk.white('Confidence:')} ${chalk.bold(formatPercent(data.confidence))}`);
        printRationale(data.rationale);
    });
});

addPredictionOptions(
    program
        .command('predict-method [organizationId]')
        .description('Прогноз метода атаки через `POST /predict/method`')
).action(async (organizationId, options) => {
    await runPrediction('/predict/method', organizationId, options, (data) => {
        printSection('Method prediction');
        console.log(`${chalk.white('Метод:')} ${chalk.cyan(data.predicted_attack_method)}`);
        console.log(`${chalk.white('Confidence:')} ${chalk.bold(formatPercent(data.confidence))}`);
        printRationale(data.rationale);
    });
});

addPredictionOptions(
    program
        .command('predict-recommendations [organizationId]')
        .description('Рекомендации через `POST /predict/recommendations`')
).action(async (organizationId, options) => {
    await runPrediction('/predict/recommendations', organizationId, options, (data) => {
        printSection('Recommendations response');
        console.log(`${chalk.white('Метод:')} ${chalk.cyan(data.predicted_attack_method)}`);
        console.log(`${chalk.white('Цель:')} ${chalk.cyan(data.predicted_target_object)}`);
        console.log(`${chalk.white('Confidence:')} ${chalk.bold(formatPercent(data.confidence))}`);
        printRecommendations(data.recommendations);
    });
});

program
    .command('vuln-map <inputFile>')
    .description('Сопоставить уязвимости через `POST /vulnerabilities/map`')
    .action(async (inputFile) => {
        try {
            const resolved = path.resolve(process.cwd(), inputFile);
            const raw = fs.readFileSync(resolved, 'utf-8');
            const parsed = JSON.parse(raw);
            const payload = Array.isArray(parsed) ? { vulnerabilities: parsed } : parsed;
            const response = await getApi().post('/vulnerabilities/map', payload);
            const data = response.data;

            if (isJsonOutput()) {
                printJson(data);
                return;
            }

            printSection('Vulnerability mapping');
            console.log(`${chalk.white('Assets:')} ${data.total_assets}`);
            console.log(`${chalk.white('Vulnerabilities:')} ${data.total_vulnerabilities}`);

            for (const item of data.items) {
                console.log(`\n${chalk.bold(item.asset_name)} ${chalk.gray(`(${item.vulnerability_code})`)}`);
                if (!item.matches.length) {
                    console.log(chalk.gray('  Нет совпадений'));
                    continue;
                }
                item.matches.slice(0, 3).forEach((match) => {
                    console.log(
                        `  ${chalk.green('•')} ${match.threat.threat_id} ${match.threat.name} ` +
                        chalk.gray(`score=${match.match_score}`)
                    );
                    console.log(chalk.gray(`    ${match.reason}`));
                });
            }
        } catch (error) {
            if (error instanceof SyntaxError) {
                console.error(chalk.red('✘ Некорректный JSON во входном файле'));
            } else if (error.code === 'ENOENT') {
                console.error(chalk.red(`✘ Файл не найден: ${inputFile}`));
            } else {
                handleApiError(error, 'Ошибка маппинга уязвимостей');
            }
            process.exitCode = 1;
        }
    });

if (!process.argv.slice(2).length) {
    program.parse(['node', 'index.js', 'welcome']);
} else {
    program.parse(process.argv);
}
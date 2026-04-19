#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { Command } = require('commander');
const chalk = require('chalk');
const axios = require('axios');
const Table = require('cli-table3');

const DEFAULT_BASE_URL = process.env.RT_API_BASE_URL || 'http://127.0.0.1:8000';
const program = new Command();

program
    .name('rt')
    .description('CLI-клиент для актуальных ручек RT Threat Analytics API')
    .version('2.0.0')
    .option('-u, --base-url <url>', 'Базовый URL API', DEFAULT_BASE_URL);

function getBaseUrl() {
    const options = program.opts();
    return (options.baseUrl || DEFAULT_BASE_URL).replace(/\/+$/, '');
}

function getApi() {
    return axios.create({
        baseURL: getBaseUrl(),
        timeout: 30000,
        headers: { 'Content-Type': 'application/json' },
    });
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

function buildPredictPayload(organizationId, options) {
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
        .requiredOption('--region <region>', 'Регион организации', 'Moscow')
        .requiredOption('--industry <industry>', 'Отрасль', 'telecom')
        .option('--season <season>', 'Сезон: winter|spring|summer|autumn', defaultSeason())
        .option('--day-of-week <number>', 'День недели: 1..7', String(defaultDayOfWeek()))
        .option('--hour <number>', 'Час: 0..23', String(defaultHour()))
        .option('--asset-type <assetType>', 'Тип актива', 'vpn_gateway')
        .option('--no-external-access', 'Отключить внешний доступ')
        .option('--privileged-accounts-count <number>', 'Количество привилегированных учеток', '12')
        .option('--known-vulnerabilities-count <number>', 'Количество известных уязвимостей', '3');
}

async function runPrediction(endpoint, organizationId, options, printer) {
    const payload = buildPredictPayload(organizationId, options);
    try {
        const response = await getApi().post(endpoint, payload);
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
            ['threats', 'Показывает `GET /threats` с фильтрами severity/category'],
            ['stats', 'Печатает сводку по `GET /stats`'],
            ['predict', 'Вызывает `POST /predict`'],
            ['predict-time', 'Вызывает `POST /predict/time`'],
            ['predict-target', 'Вызывает `POST /predict/target`'],
            ['predict-method', 'Вызывает `POST /predict/method`'],
            ['predict-recommendations', 'Вызывает `POST /predict/recommendations`'],
            ['vuln-map', 'Вызывает `POST /vulnerabilities/map` из JSON-файла'],
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

addPredictionOptions(
    program
        .command('predict <organizationId>')
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
        .command('predict-time <organizationId>')
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
        .command('predict-target <organizationId>')
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
        .command('predict-method <organizationId>')
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
        .command('predict-recommendations <organizationId>')
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
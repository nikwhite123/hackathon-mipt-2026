#!/usr/bin/env node

const { Command } = require('commander');
const chalk = require('chalk');
const axios = require('axios');
const Table = require('cli-table3');

const program = new Command();


program
    .name('rt-infra')
    .description('Инструмент командной строки RT Infra Security')
    .version('1.0.0');

program
    .command('status')
    .description('Проверить доступность систем')
    .action(async () => {
        console.log(chalk.gray('Проверка связи с бэкендом Rostelecom...'));
        try {
            const response = await axios.get('http://localhost:8001/health');
            if (response.data.status === 'ok') {
                console.log(chalk.green('✔ Система мониторинга онлайн'));
                console.log(chalk.white(`Версия API: 2.1.0`));
            }
        } catch (error) {
            console.log(chalk.red('✘ Ошибка: Бэкенд недоступен'));
            console.log(chalk.yellow('Запустите сервер: uvicorn main:app --reload --port 8000'));
        }
    });

    program
    .command('threats')
    .description('Показать реестр угроз')
    .action(async () => {
        try {
            const response = await axios.get('http://localhost:8001/threats');
            const threats = response.data.items;

            const table = new Table({
                head: [chalk.cyan('ID'), chalk.cyan('Название'), chalk.cyan('Уровень')],
                colWidths: [12, 50, 15]
            });

            threats.forEach(t => {
                let sevColor = chalk.white;
                if (t.severity === 'critical') sevColor = chalk.red.bold;
                if (t.severity === 'high') sevColor = chalk.red;
                if (t.severity === 'medium') sevColor = chalk.yellow;

                table.push([
                    t.threat_id, 
                    t.name, 
                    sevColor(t.severity.toUpperCase())
                ]);
            });

            console.log(table.toString());
            console.log(chalk.gray(`Всего записей: ${response.data.total}`));
        } catch (error) {
            console.log(chalk.red('✘ Ошибка при получении реестра угроз.'));
        }
    });

    program
    .command('stats')
    .description('Краткая сводка аналитики по угрозам')
    .action(async () => {
        try {
            const response = await axios.get('http://localhost:8001/stats');
            const d = response.data;

            console.log(chalk.bold.hex('#7733FF')('\n--- СВОДНАЯ СТАТИСТИКА RT INFRA ---'));
            
            console.log(`${chalk.white('Всего инцидентов:')} ${chalk.bold(d.total_incidents)}`);
            console.log(`${chalk.white('Топ метод атаки:')}  ${chalk.red(d.top_attack_method.toUpperCase())}`);
            console.log(`${chalk.white('Основная цель:')}    ${chalk.cyan(d.top_target_object.toUpperCase())}`);
            
            console.log(chalk.gray('\nРаспределение по рискам:'));
            const r = d.risk_score_distribution || d.risk_distribution;
            console.log(`${chalk.red('  Critical:')} ${r.critical}`);
            console.log(`${chalk.red('  High:')}     ${r.high}`);
            console.log(`${chalk.yellow('  Medium:')}   ${r.medium}`);
            console.log(`${chalk.green('  Low:')}      ${r.low}`);

            console.log(chalk.gray('\nТоп целей по объектам:'));
            const targets = d.incidents_by_target_object;
            Object.entries(targets)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 3)                
                .forEach(([name, count]) => {
                    console.log(`  • ${name.padEnd(12)} : ${count}`);
                });

            console.log(chalk.bold.hex('#7733FF')('-----------------------------------\n'));
        } catch (error) {
            console.log(chalk.red('✘ Ошибка получения статистики.'));
        }
    });

    program
    .command('predict <org_id>')
    .action(async (orgId) => {
        console.log(chalk.magenta(`📡 Анализ векторов атак для ID: ${orgId}...`));
        try {
            const response = await axios.post('http://localhost:8001/predict', {
                organization_id: orgId,
                infrastructure_type: "hybrid",
                industry: "finance",
                region: "Moscow",
                season: "spring",
                day_of_week: 3,
                hour: 12,
                asset_type: "db_server",
                privileged_accounts_count: 5,
                known_vulnerabilities_count: 10
            });

            const data = response.data;

            console.log(chalk.bold.green('\n✔ Прогноз сформирован успешно:'));
            console.log(chalk.white('--------------------------------------------------'));
            
            const probability = (data.risk_score * 100).toFixed(0);
            const target = data.predicted_target_object;
            const method = data.predicted_attack_method;
            const time = data.predicted_attack_time_window;

            console.log(`Вероятность:  ${chalk.red.bold(probability + '%')}`);
            console.log(`Цель атаки:   ${chalk.cyan(target.toUpperCase())}`);
            console.log(`Метод:        ${chalk.cyan(method.replace('_', ' ').toUpperCase())}`);
            console.log(`Окно атаки:   ${chalk.yellow(time)}`);
            console.log(`Уверенность ML: ${chalk.gray(data.confidence * 100 + '%')}`);
            
            console.log(chalk.white('\nОбоснование (Rationale):'));
            data.rationale.forEach(line => {
                console.log(chalk.gray(` • ${line}`));
            });

            if (data.recommendations && data.recommendations.length > 0) {
                console.log(chalk.bold.yellow('\nРекомендации по защите:'));
                data.recommendations.forEach(rec => {
                    console.log(`${chalk.green('✔')} ${chalk.white(rec.title)} ${chalk.gray('(' + rec.code + ')')}`);
                });
            }
            
            console.log(chalk.white('--------------------------------------------------'));

        } catch (error) {
            console.log(chalk.red('✘ Ошибка при генерации прогноза.'));
            if (error.response?.data?.errors) {
                console.dir(error.response.data.errors, { depth: null });
            }
        }
    });

program.parse();
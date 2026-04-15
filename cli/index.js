#!/usr/bin/env node

const { Command } = require('commander');
const chalk = require('chalk');
const axios = require('axios');

const program = new Command();

program
    .name('rt-infra')
    .description('Инструмент командной строки RT Infra Security')
    .version('1.0.0');

program
    .command('status')
    .description('Проверить доступность систем')
    .action(async () => {
        console.log(chalk.gray('Проверка связи с бэкендом...'));
        try {
            const response = await axios.get('http://localhost:5173/api/status');
            console.log(chalk.green('✔ Бэкенд онлайн'));
            console.log(chalk.white(`Статус: ${response.data.status}`));
        } catch (error) {
            console.log(chalk.red('✘ Ошибка: Бэкенд недоступен'));
            console.log(chalk.yellow('Убедитесь, что сервер запущен на порту 5000'));
        }
    });

program.parse();
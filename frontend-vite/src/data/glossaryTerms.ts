/**
 * Curated glossary entries for the Glossary page (static content).
 */
export type TermCategory = 'term' | 'threat' | 'vulnerability';

export interface Term {
    key: string;
    title: string;
    description: string;
    letter: string;
    category: TermCategory;
}

export const glossaryTerms: Term[] = [
    {
        key: '1',
        title: 'DDoS (Distributed Denial of Service)',
        description: 'Атака, при которой сервер или сайт перегружается огромным количеством запросов с множества устройств одновременно, делая его недоступным для обычных пользователей.',
        letter: 'D',
        category: 'threat',
    },
    {
        key: '2',
        title: 'DoS (Denial of Service)',
        description: 'Атака на отказ в обслуживании — один компьютер или скрипт перегружает сервер запросами, чтобы он не мог отвечать легитимным пользователям.',
        letter: 'D',
        category: 'threat',
    },
    {
        key: '3',
        title: 'SQL Injection',
        description: 'Внедрение вредоносного SQL-кода через формы или URL, чтобы получить доступ к базе данных, украсть данные или изменить их.',
        letter: 'S',
        category: 'vulnerability',
    },
    {
        key: '4',
        title: 'XSS (Cross-Site Scripting)',
        description: 'Атака, при которой злоумышленник внедряет вредоносный JavaScript-код на страницу сайта, который выполняется у других пользователей.',
        letter: 'X',
        category: 'vulnerability',
    },
    {
        key: '5',
        title: 'CSRF (Cross-Site Request Forgery)',
        description: 'Атака, при которой пользователя заставляют выполнить нежелательное действие на сайте (например, перевод денег), пока он авторизован.',
        letter: 'C',
        category: 'vulnerability',
    },
    {
        key: '6',
        title: 'Brute Force Attack',
        description: 'Перебор паролей или ключей методом «грубой силы» — автоматическая попытка всех возможных комбинаций до успеха.',
        letter: 'B',
        category: 'threat',
    },
    {
        key: '7',
        title: 'MITM (Man-in-the-Middle)',
        description: 'Атака «посредника» — злоумышленник перехватывает и может читать или изменять данные между пользователем и сервером.',
        letter: 'M',
        category: 'threat',
    },
    {
        key: '8',
        title: 'Phishing',
        description: 'Социальная инженерия: обман пользователя через поддельные письма или сайты, чтобы выманить логины, пароли или другие данные.',
        letter: 'P',
        category: 'threat',
    },
    {
        key: '9',
        title: 'Ransomware',
        description: 'Вредоносное ПО, которое шифрует файлы или блокирует доступ к серверу и требует выкуп за восстановление.',
        letter: 'R',
        category: 'threat',
    },
    {
        key: '10',
        title: 'Zero-Day Exploit',
        description: 'Атака, использующая уязвимость, о которой разработчики ещё не знают и не успели выпустить патч.',
        letter: 'Z',
        category: 'vulnerability',
    },
    {
        key: '11',
        title: 'SYN Flood',
        description: 'Вид DDoS-атаки, при которой сервер засыпают полуоткрытыми TCP-соединениями, исчерпывая ресурсы на обработку новых подключений.',
        letter: 'S',
        category: 'threat',
    },
    {
        key: '12',
        title: 'Credential Stuffing',
        description: 'Атака, при которой используются украденные пары логин/пароль из других утечек для входа на разные сервисы.',
        letter: 'C',
        category: 'threat',
    },
];
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
        title: 'False consensus bias',
        description:
            'In psychology, the false consensus effect is a cognitive bias...',
        letter: 'F',
        category: 'term',
    },
    {
        key: '2',
        title: 'Framework',
        description: 'A reusable structure for building software systems.',
        letter: 'F',
        category: 'term',
    },
    {
        key: '3',
        title: 'Figma',
        description: 'A cloud-based design tool used for UI/UX.',
        letter: 'F',
        category: 'term',
    },
    {
        key: '4',
        title: 'False consensus bias',
        description:
            'In psychology, the false consensus effect is a cognitive bias...',
        letter: 'F',
        category: 'term',
    },
    {
        key: '5',
        title: 'Aramework',
        description: 'A reusable structure for building software systems.',
        letter: 'A',
        category: 'term',
    },
    {
        key: '6',
        title: 'Yigma',
        description: 'A cloud-based design tool used for UI/UX.',
        letter: 'Y',
        category: 'term',
    },
];
import React, {useState} from 'react';
import {Input, Button, Collapse, Typography} from 'antd';
import {SearchOutlined} from '@ant-design/icons';
import {glossaryTerms} from "../../data/glossaryTerms.ts";

const {Title, Text} = Typography;
const {Panel} = Collapse;

const terms = glossaryTerms;

const Glossary: React.FC = () => {
    const [searchTerm, setSearchTerm] = useState<string>('');
    const [selectedLetter, setSelectedLetter] = useState<string>('F');

    const filteredTerms = terms.filter((term) => {
        const matchesSearch = term.title.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesLetter = term.letter === selectedLetter;

        return matchesSearch && matchesLetter;
    });

    return (
        <div style={{maxWidth: 900, margin: '40px auto', padding: '0 20px'}}>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24}}>
                <Title level={1} style={{margin: 0}}>
                    Глоссарий
                </Title>
                <div style={{display: 'flex', alignItems: 'center', gap: 12}}>

                </div>
            </div>

            <div style={{display: 'flex', gap: 12, marginBottom: 24}}>
                <Input
                    placeholder="Поиск по термину"
                    prefix={<SearchOutlined/>}
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    size="large"
                    style={{flex: 1}}
                />
                <Button type="primary" size="large">
                    Поиск
                </Button>
            </div>

            <div
                style={{
                    display: 'flex',
                    gap: 8,
                    marginBottom: 24,
                    flexWrap: 'wrap',
                }}
            >
                {Array.from('ABCDEFGHIJKLMNOPQRSTUVWXYZ').map((letter) => (
                    <Button
                        key={letter}
                        type={letter === selectedLetter ? 'primary' : 'default'}
                        style={{width: 40}}
                        onClick={() => setSelectedLetter(letter)} // 🔥 ВАЖНО
                    >
                        {letter}
                    </Button>
                ))}
            </div>

            <Collapse
                accordion
                style={{backgroundColor: '#fff'}}
            >
                {filteredTerms.map((term) => (
                    <Panel
                        header={
                            <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                                <div
                                    style={{
                                        width: 24,
                                        height: 24,
                                        backgroundColor: '#1890ff',
                                        color: 'white',
                                        borderRadius: '50%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        fontSize: '14px',
                                        fontWeight: 'bold',
                                    }}
                                >
                                    {term.letter}
                                </div>
                                <Text strong style={{fontSize: '16px'}}>
                                    {term.title}
                                </Text>
                            </div>
                        }
                        key={term.key}
                    >
                        <Text style={{fontSize: '15px', lineHeight: '1.6'}}>
                            {term.description || 'Описание пока отсутствует...'}
                        </Text>
                    </Panel>
                ))}
            </Collapse>

            {filteredTerms.length === 0 && (
                <div style={{textAlign: 'center', padding: '60px 20px', color: '#999'}}>
                    Ничего не найдено по запросу "{searchTerm}"
                </div>
            )}
        </div>
    );
};

export default Glossary;
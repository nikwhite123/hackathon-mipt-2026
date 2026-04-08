import React, { useState, useEffect } from 'react';
import { Input, Button, Collapse, Typography, Tabs, Tag, Space, Spin } from 'antd';
import { SearchOutlined, BookOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import { glossaryTerms } from "../../data/glossaryTerms.ts";
import { threatService } from "../../api/threatService";
import type { IThreat }  from "../../api/threatService";

const { Title, Text } = Typography;
const { Panel } = Collapse;

const Glossary: React.FC = () => {
    // Состояния для терминов
    const [searchTerm, setSearchTerm] = useState<string>('');
    const [selectedLetter, setSelectedLetter] = useState<string>('F');
    
    // Состояния для угроз ФСТЭК
    const [threats, setThreats] = useState<IThreat[]>([]);
    const [loadingThreats, setLoadingThreats] = useState<boolean>(false);

    useEffect(() => {
        threatService.getThreats()
            .then(data => setThreats(data.items))
            .catch(err => console.error("Ошибка загрузки угроз:", err))
            .finally(() => setLoadingThreats(false));
    }, []);

    const filteredTerms = glossaryTerms.filter((term) => {
        const matchesSearch = term.title.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesLetter = selectedLetter ? term.letter === selectedLetter : true;
        return matchesSearch && matchesLetter;
    });

    // Отрисовка контента терминов
    const renderTerms = () => (
        <>
            <div style={{ display: 'flex', gap: 12, marginBottom: 24, marginTop: 24 }}>
                <Input
                    placeholder="Поиск по термину"
                    prefix={<SearchOutlined />}
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    size="large"
                    style={{ flex: 1 }}
                />
            </div>
            <div style={{ display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap' }}>
                <Button 
                    onClick={() => {setSearchTerm(''); setSelectedLetter('')}}
                    style={{ fontWeight: 'bold' }}
                >
                    Все
                </Button>
                {Array.from('ABCDEFGHIJKLMNOPQRSTUVWXYZ').map((letter) => (
                    <Button
                        key={letter}
                        type={letter === selectedLetter ? 'primary' : 'default'}
                        style={{ width: 40, padding: 0 }}
                        onClick={() => setSelectedLetter(letter)}
                    >
                        {letter}
                    </Button>
                ))}
            </div>
            <Collapse accordion style={{ backgroundColor: '#fff' }}>
                {filteredTerms.map((term) => (
                    <Panel 
                        header={<Text strong>{term.title}</Text>} 
                        key={term.key}
                        extra={<Tag color="blue">{term.letter}</Tag>}
                    >
                        <Text>{term.description || 'Описание отсутствует...'}</Text>
                    </Panel>
                ))}
            </Collapse>
        </>
    );

    // Отрисовка контента угроз ФСТЭК
    const renderThreats = () => (
        <Spin spinning={loadingThreats}>
            <div style={{ marginTop: 24 }}>
                <Collapse accordion style={{ backgroundColor: '#fff' }}>
                    {threats.map((threat) => (
                        <Panel 
                            header={
                                <Space>
                                    <Tag color={threat.severity === 'critical' || threat.severity === 'high' ? 'volcano' : 'green'}>
                                        {threat.threat_id}
                                    </Tag>
                                    <Text strong>{threat.name}</Text>
                                </Space>
                            } 
                            key={threat.threat_id}
                        >
                            <div style={{ padding: '4px 0' }}>
                                <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
                                    {threat.description}
                                </Text>
                                <Space direction="vertical" size={0}>
                                    <div><Text strong>Категория: </Text><Tag>{threat.category}</Tag></div>
                                    <div style={{ marginTop: 8 }}>
                                        <Text strong>Методы атак: </Text>
                                        {threat.common_methods.map(m => <Tag key={m} color="blue">{m}</Tag>)}
                                    </div>
                                    <div style={{ marginTop: 8 }}>
                                        <Text strong>Цели: </Text>
                                        {threat.likely_targets.map(t => <Tag key={t} color="purple">{t}</Tag>)}
                                    </div>
                                </Space>
                            </div>
                        </Panel>
                    ))}
                </Collapse>
            </div>
        </Spin>
    );

    return (
        <div style={{ maxWidth: 900, margin: '40px auto', padding: '0 20px' }}>
            <Title level={1} style={{ marginBottom: 32 }}>База знаний</Title>
            
            <Tabs 
                defaultActiveKey="1"
                items={[
                    {
                        key: '1',
                        label: <span><BookOutlined /> Термины</span>,
                        children: renderTerms(),
                    },
                    {
                        key: '2',
                        label: <span><SafetyCertificateOutlined /> Реестр угроз ФСТЭК</span>,
                        children: renderThreats(),
                    },
                ]}
            />
        </div>
    );
};

export default Glossary;
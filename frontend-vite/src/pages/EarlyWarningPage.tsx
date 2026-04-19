/**
 * Early warning: runs `/predict` from current org settings and shows forecast UI.
 */
import {Alert, Modal, Progress, Statistic, Typography, List, Badge, Button, Spin, message, Space} from "antd"
import {useEffect, useMemo, useRef, useState} from "react"
import {useThreatForecast} from "../hooks/useThreatForecast"
import {useAuthStore} from "../store/authStore"
import RTCard from "../ui/RTCard"
import style from "../Styles/HomePage.module.css"

import type {IRecommendation} from "../types/incident.types"

export default function EarlyWarningPage() {
    const {user} = useAuthStore()
    const [visible, setVisible] = useState(false)
    const [preferMl, setPreferMl] = useState(false)
    const {data: threat, loading, error: loadError} = useThreatForecast({enabled: !!user, preferMl})
    const prevToastErr = useRef<string | null>(null)

    useEffect(() => {
        if (loadError && loadError !== prevToastErr.current) {
            prevToastErr.current = loadError
            message.error(loadError)
        }
        if (!loadError) prevToastErr.current = null
    }, [loadError])

    const stats = useMemo(() => ({
        probability: Math.round((threat?.confidence ?? 0) * 100),
        riskScore: Math.round((threat?.risk_score ?? 0) * 100),
        target: threat?.predicted_target_object?.toUpperCase() ?? "—",
        method: threat?.predicted_attack_method ?? "—",
        window: threat?.predicted_attack_time_window ?? "—"
    }), [threat])

    return (
        <div className={style.infraEarlyRow} style={{marginTop: '16px'}}>
            {loadError ? (
                <RTCard>
                    <Alert type="error" message="Прогноз недоступен" description={loadError} showIcon/>
                </RTCard>
            ) : null}
            <RTCard>
                <Spin spinning={loading}>
                    <Typography.Paragraph type="secondary" style={{marginBottom: 12, fontSize: 12}}>
                        Risk score считается на сервере из числа уязвимостей (зависит от хостов и технологий в форме),
                        интенсивности атак по истории вашей организации (регион, сезон, час и при возможности —
                        отрасль),
                        критичности выбранного актива и внешнего доступа. По умолчанию используется эвристический
                        прогноз.
                        По кнопке ниже можно отдельно запросить ML-версию метода и цели атаки, не меняя risk score и
                        окно атаки.
                    </Typography.Paragraph>
                    <Space style={{marginBottom: 8}} wrap>
                        <Button type={preferMl ? "default" : "primary"} onClick={() => setPreferMl(false)}>
                            Эвристический прогноз
                        </Button>
                        <Button type={preferMl ? "primary" : "default"} onClick={() => setPreferMl(true)}>
                            Получить ML-прогноз
                        </Button>
                    </Space>
                    <Typography.Text type="secondary" style={{display: "block", marginBottom: 12, fontSize: 12}}>
                        ML-режим меняет только метод и цель атаки. Risk score и окно атаки остаются эвристическими.
                    </Typography.Text>
                    <Space align="center" style={{marginBottom: 12}} wrap>
                        <Typography.Text type="secondary" style={{fontSize: 12}}>
                            {preferMl ? "Сейчас отображается ML-прогноз для метода и цели атаки." : "Сейчас отображается эвристический прогноз."}
                        </Typography.Text>
                    </Space>
                    <Statistic
                        title="Уровень угрозы (Risk Score)"
                        value={stats.riskScore}
                        suffix="%"
                        valueStyle={{color: stats.riskScore > 60 ? '#FF4F12' : '#7733FF'}}
                    />
                    <div className={style.infraEarlyProgressContainer}>
                        <Progress
                            percent={stats.riskScore}
                            status={stats.riskScore > 70 ? "exception" : "active"}
                            strokeColor={stats.riskScore > 60 ? '#FF4F12' : '#7733FF'}
                        />
                    </div>
                    <Typography.Text type="secondary">Окно атаки: {stats.window}</Typography.Text>
                </Spin>
            </RTCard>

            <RTCard hoverable onClick={() => setVisible(true)}>
                <Spin spinning={loading}>
                    <div className={style.infraEarlyContent}>
                        <div style={{flex: 1}}>
                            <Alert
                                message={`Цель: ${stats.target}`}
                                description={`Метод: ${stats.method}`}
                                type={stats.riskScore > 60 ? "error" : "warning"}
                                showIcon
                            />
                        </div>

                        <div className={style.infraEarlyStatsGrid}>
                            <Statistic title="Точность прогноза" value={stats.probability} suffix="%"/>
                            <Button type="primary" onClick={() => setVisible(true)}>
                                Посмотреть меры защиты
                            </Button>
                        </div>
                    </div>
                </Spin>
            </RTCard>

            <Modal
                open={visible}
                onCancel={() => setVisible(false)}
                footer={null}
                title="Рекомендации по противодействию"
                width={600}
            >
                <List
                    itemLayout="horizontal"
                    dataSource={threat?.recommendations ?? []}
                    renderItem={(item: IRecommendation) => (
                        <List.Item>
                            <List.Item.Meta
                                avatar={
                                    <Badge
                                        count={item.priority}
                                        style={{backgroundColor: item.priority === 1 ? '#FF4F12' : '#7733FF'}}
                                    />
                                }
                                title={item.title}
                                description={item.description}
                            />
                        </List.Item>
                    )}
                />
                {threat?.rationale && (
                    <div style={{marginTop: 16, padding: '12px', background: '#f5f5f5', borderRadius: '8px'}}>
                        <Typography.Text strong>Обоснование системы:</Typography.Text>
                        <ul>
                            {threat.rationale.map((r: string, i: number) => (
                                <li key={i}><small>{r}</small></li>
                            ))}
                        </ul>
                    </div>
                )}
            </Modal>
        </div>
    )
}
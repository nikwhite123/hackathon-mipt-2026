/**
 * Modal for login, registration, and organization code resolution before sign-up.
 */
import React, { useEffect, useState } from "react";
import { Modal, Form, Input, Button, Typography, message } from "antd";
import { UserOutlined, LockOutlined, ClusterOutlined, MailOutlined, SearchOutlined } from "@ant-design/icons";
import { fetchOrganizationByCode, login, register } from "../../api/authService";
import type { AuthUser, OrganizationOption } from "../../types/auth";

interface AuthModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (user: AuthUser) => void;
}

const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onSuccess }) => {
    const [isLoginView, setIsLoginView] = useState(true);
    const [resolvedOrg, setResolvedOrg] = useState<OrganizationOption | null>(null);
    const [resolvingOrg, setResolvingOrg] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [form] = Form.useForm();

    useEffect(() => {
        if (!isOpen) return
        setResolvedOrg(null)
        form.setFieldsValue({ organization_code: undefined })
    }, [isOpen, isLoginView, form])

    const handleFinish = async (values: Record<string, string | number>) => {
        setSubmitting(true)
        try {
            if (isLoginView) {
                const response = await login({
                    email: String(values.email),
                    password: String(values.password),
                })
                onSuccess(response.user)
                message.success("Вход выполнен")
            } else {
                await register({
                    first_name: String(values.first_name),
                    last_name: String(values.last_name),
                    email: String(values.email),
                    password: String(values.password),
                    organization_code: String(values.organization_code || "").trim(),
                })
                const response = await login({
                    email: String(values.email),
                    password: String(values.password),
                })
                onSuccess(response.user)
                message.success("Регистрация завершена")
            }
            form.resetFields()
            onClose()
        } catch (error: unknown) {
            console.error("Ошибка авторизации:", error)
            const detail =
                typeof error === "object" &&
                error !== null &&
                "response" in error &&
                typeof (error as { response?: { data?: { detail?: string } } }).response?.data?.detail === "string"
                    ? (error as { response: { data: { detail: string } } }).response.data.detail
                    : null
            message.error(detail || "Не удалось выполнить авторизацию")
        } finally {
            setSubmitting(false)
        }
    }

    return (
        <Modal
            title={isLoginView ? "Авторизация" : "Регистрация"}
            open={isOpen}
            onCancel={onClose}
            footer={null}
            centered
            destroyOnClose
        >
            <Form
                form={form}
                name="auth_form"
                layout="vertical"
                onFinish={handleFinish}
                style={{ marginTop: '20px' }}
            >
                <Form.Item
                    name="email"
                    rules={[
                        { required: true, message: "Введите email!" },
                        { type: "email", message: "Некорректный формат email" },
                    ]}
                >
                    <Input prefix={<MailOutlined />} placeholder="Email" size="large" autoComplete="email" />
                </Form.Item>

                <Form.Item
                    name="password"
                    rules={[
                        { required: true, message: "Введите пароль!" },
                        ...(isLoginView
                            ? []
                            : [
                                  { min: 10, message: "Минимум 10 символов" },
                                  {
                                      pattern: /^(?=.*[a-zа-яё])(?=.*[A-ZА-ЯЁ])(?=.*\d).+$/,
                                      message: "Пароль: латиница/кириллица, заглавная, строчная и цифра",
                                  },
                              ]),
                    ]}
                >
                    <Input.Password
                        prefix={<LockOutlined />}
                        placeholder={isLoginView ? "Пароль" : "Пароль (10+, заглавная, строчная, цифра)"}
                        size="large"
                        autoComplete={isLoginView ? "current-password" : "new-password"}
                    />
                </Form.Item>

                {!isLoginView && (
                    <>
                        <Form.Item
                            name="first_name"
                            rules={[
                                { required: true, message: "Введите имя!" },
                                { min: 2, message: "Минимум 2 символа" },
                                {
                                    validator: async (_, value: string) => {
                                        const s = (value || "").trim()
                                        if (s && !/[a-zA-Zа-яА-ЯёЁ]/.test(s)) {
                                            throw new Error("Имя должно содержать буквы")
                                        }
                                    },
                                },
                            ]}
                        >
                            <Input prefix={<UserOutlined />} placeholder="Имя" size="large" autoComplete="given-name" />
                        </Form.Item>

                        <Form.Item
                            name="last_name"
                            rules={[
                                { required: true, message: "Введите фамилию!" },
                                { min: 2, message: "Минимум 2 символа" },
                                {
                                    validator: async (_, value: string) => {
                                        const s = (value || "").trim()
                                        if (s && !/[a-zA-Zа-яА-ЯёЁ]/.test(s)) {
                                            throw new Error("Фамилия должна содержать буквы")
                                        }
                                    },
                                },
                            ]}
                        >
                            <Input prefix={<UserOutlined />} placeholder="Фамилия" size="large" autoComplete="family-name" />
                        </Form.Item>

                        <Form.Item label="Код организации">
                            <Input.Group compact style={{ display: "flex" }}>
                                <Form.Item
                                    name="organization_code"
                                    noStyle
                                    rules={[{ required: true, message: "Введите код организации" }]}
                                >
                                    <Input
                                        style={{ flex: 1 }}
                                        placeholder="Код из приглашения"
                                        size="large"
                                        suffix={<ClusterOutlined />}
                                        onChange={() => setResolvedOrg(null)}
                                    />
                                </Form.Item>
                                <Button
                                    type="default"
                                    size="large"
                                    icon={<SearchOutlined />}
                                    loading={resolvingOrg}
                                    onClick={async () => {
                                        const code = String(form.getFieldValue("organization_code") || "").trim()
                                        if (!code) {
                                            message.warning("Введите код организации")
                                            return
                                        }
                                        setResolvingOrg(true)
                                        try {
                                            const org = await fetchOrganizationByCode(code)
                                            setResolvedOrg(org)
                                            message.success(org.name ? `${org.name}` : "Организация найдена")
                                        } catch {
                                            setResolvedOrg(null)
                                            message.error("Организация не найдена")
                                        } finally {
                                            setResolvingOrg(false)
                                        }
                                    }}
                                >
                                    Проверить
                                </Button>
                            </Input.Group>
                        </Form.Item>
                        {resolvedOrg ? (
                            <Typography.Paragraph type="secondary" style={{ marginTop: -8 }}>
                                {resolvedOrg.code ? `${resolvedOrg.name} (${resolvedOrg.code})` : resolvedOrg.name}
                            </Typography.Paragraph>
                        ) : null}
                    </>
                )}

                <Form.Item>
                    <Button
                        type="primary"
                        htmlType="submit"
                        block
                        size="large"
                        loading={submitting}
                        style={{ backgroundColor: '#7733FF', borderColor: '#7733FF' }}
                    >
                        {isLoginView ? "Войти" : "Зарегистрироваться"}
                    </Button>
                    <div style={{ textAlign: 'center', marginTop: '12px' }}>
                        <Typography.Link onClick={() => setIsLoginView(!isLoginView)}>
                            {isLoginView ? "Нет аккаунта? Создать" : "Уже есть аккаунт? Войти"}
                        </Typography.Link>
                    </div>
                </Form.Item>
            </Form>
        </Modal>
    );
};

export default AuthModal;
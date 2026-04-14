import React, { useState } from "react";
import { Modal, Form, Input, Button, Typography } from "antd";
import { UserOutlined, LockOutlined, ClusterOutlined } from "@ant-design/icons";

interface AuthModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (username: string) => void;
}

const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onSuccess }) => {
    const [isLoginView, setIsLoginView] = useState(true);

    const handleFinish = (values: any) => {
        console.log("Auth Values:", values);
        onSuccess(values.username);
        onClose();
    };

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
                name="auth_form"
                layout="vertical"
                onFinish={handleFinish}
                style={{ marginTop: '20px' }}
            >
                <Form.Item
                    name="username"
                    rules={[{ required: true, message: 'Введите логин!' }]}
                >
                    <Input prefix={<UserOutlined />} placeholder="Логин" size="large" />
                </Form.Item>

                <Form.Item
                    name="password"
                    rules={[{ required: true, message: 'Введите пароль!' }]}
                >
                    <Input.Password prefix={<LockOutlined />} placeholder="Пароль" size="large" />
                </Form.Item>

                {!isLoginView && (
                    <Form.Item
                        name="organization"
                        rules={[{ required: true, message: 'Введите ID организации!' }]}
                    >
                        <Input prefix={<ClusterOutlined />} placeholder="ID Организации" size="large" />
                    </Form.Item>
                )}

                <Form.Item>
                    <Button
                        type="primary"
                        htmlType="submit"
                        block
                        size="large"
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
import { useLogin } from "@refinedev/core";
import { Alert, Button, Card, Form, Input, Typography } from "antd";

type LoginValues = {
  identifier: string;
  password: string;
  remember_me?: boolean;
};

export function LoginPage() {
  const { mutate: login, isPending, error } = useLogin<LoginValues>();

  const onFinish = (values: LoginValues) => {
    login(values);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 16,
      }}
    >
      <Card title="Вход в админ-панель" style={{ width: 420, maxWidth: "100%" }}>
        <Form<LoginValues> layout="vertical" onFinish={onFinish} initialValues={{ remember_me: false }}>
          <Form.Item
            label="Логин или Email"
            name="identifier"
            rules={[{ required: true, message: "Введите логин или email" }]}
          >
            <Input autoComplete="username" placeholder="admin или admin@example.com" />
          </Form.Item>
          <Form.Item label="Пароль" name="password" rules={[{ required: true, message: "Введите пароль" }]}>
            <Input.Password autoComplete="current-password" />
          </Form.Item>
          {error?.message ? (
            <Form.Item>
              <Alert message="Ошибка входа" description={error.message} type="error" showIcon />
            </Form.Item>
          ) : null}
          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" loading={isPending} block>
              Войти
            </Button>
          </Form.Item>
          <Typography.Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
            Поддерживается вход как по логину, так и по email.
          </Typography.Paragraph>
        </Form>
      </Card>
    </div>
  );
}

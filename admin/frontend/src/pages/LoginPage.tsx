import { useLogin } from "@refinedev/core";
import { Alert, Button, Card, Checkbox, Form, Input, Typography, message } from "antd";
import { getApiUrl } from "../refine/providers";

type LoginValues = {
  identifier: string;
  password: string;
  remember_me?: boolean;
};

export function LoginPage() {
  const { mutate: login, isPending, error } = useLogin<LoginValues>();
  const [form] = Form.useForm<LoginValues>();

  const onFinish = (values: LoginValues) => {
    login(values);
  };
  const requestReset = async () => {
    const identifier = form.getFieldValue("identifier");
    if (!identifier) {
      message.warning("Введите логин или email для восстановления.");
      return;
    }
    const response = await fetch(`${getApiUrl()}/auth/request-reset`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier }),
    });
    if (!response.ok) {
      message.error("Не удалось запросить восстановление.");
      return;
    }
    const payload = (await response.json()) as { data?: { reset_token?: string } };
    message.success(payload.data?.reset_token ? `Токен для dev: ${payload.data.reset_token}` : "Запрос отправлен.");
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
        <Form<LoginValues> form={form} layout="vertical" onFinish={onFinish} initialValues={{ remember_me: false }}>
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
          <Form.Item name="remember_me" valuePropName="checked">
            <Checkbox>Запомнить меня на этом устройстве</Checkbox>
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
          <Button type="link" style={{ paddingLeft: 0 }} onClick={requestReset}>
            Не помню пароль
          </Button>
        </Form>
      </Card>
    </div>
  );
}

import { Create, DeleteButton, Edit, EditButton, List, SaveButton, useForm, useTable } from "@refinedev/antd";
import { Form, Input, InputNumber, Select, Switch, Table, Typography } from "antd";
type UserRecord = {
  id: number;
  username: string | null;
  full_name?: string | null;
  phone_number?: string | null;
  establishment: string;
  user_type?: string;
  first_name?: string | null;
  last_name?: string | null;
  birth_date?: string | null;
  position?: string | null;
  is_active?: boolean;
};

export function ManagersList() {
  const { tableProps } = useTable<UserRecord>({ resource: "users" });

  return (
    <List
      title="Менеджеры"
      description="Контакты пользователей бота: ФИО, телефон, Telegram, заведения. Можно создавать, редактировать и удалять."
      createButtonProps={{ size: "middle" }}
    >
      <Table
        {...tableProps}
        rowKey={(record) => String(record.id)}
        pagination={{ pageSize: 20, showSizeChanger: true }}
      >
        <Table.Column dataIndex="full_name" title="ФИО" render={(v) => v || "—"} />
        <Table.Column dataIndex="phone_number" title="Телефон" render={(v) => v || "—"} />
        <Table.Column<UserRecord>
          title="Telegram"
          key="telegram"
          render={(_, record) => {
            if (record.username) {
              return (
                <a href={`https://t.me/${record.username}`} target="_blank" rel="noopener noreferrer">
                  @{record.username}
                </a>
              );
            }
            return <Typography.Text type="secondary">ID: {record.id}</Typography.Text>;
          }}
        />
        <Table.Column dataIndex="establishment" title="Заведение" />
        <Table.Column<UserRecord>
          title="Действия"
          width={120}
          render={(_, record) => (
            <>
              <EditButton hideText size="small" recordItemId={record.id} />
              <DeleteButton resource="users" hideText size="small" recordItemId={record.id} />
            </>
          )}
        />
      </Table>
    </List>
  );
}

const userTypeOptions = [
  { label: "HoReCa", value: "horeca" },
  { label: "Розница", value: "retail" },
];

export function ManagersCreate() {
  const { formProps, saveButtonProps } = useForm<UserRecord>({ resource: "users", action: "create" });

  return (
    <Create title="Новый менеджер (пользователь)" saveButtonProps={saveButtonProps}>
      <Form {...formProps} layout="vertical">
        <Form.Item label="ID (Telegram)" name="id" rules={[{ required: true }]}>
          <InputNumber style={{ width: "100%" }} placeholder="Числовой ID из Telegram" />
        </Form.Item>
        <Form.Item label="Логин" name="username">
          <Input placeholder="@username" />
        </Form.Item>
        <Form.Item label="ФИО" name="full_name">
          <Input />
        </Form.Item>
        <Form.Item label="Телефон" name="phone_number">
          <Input placeholder="+7..." />
        </Form.Item>
        <Form.Item label="Тип" name="user_type" rules={[{ required: true }]}>
          <Select options={userTypeOptions} />
        </Form.Item>
        <Form.Item label="Заведение" name="establishment" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="Активен" name="is_active" valuePropName="checked" initialValue={true}>
          <Switch />
        </Form.Item>
      </Form>
      <SaveButton {...saveButtonProps}>Сохранить</SaveButton>
    </Create>
  );
}

export function ManagersEdit() {
  const { formProps, saveButtonProps } = useForm<UserRecord>({ resource: "users", action: "edit" });

  return (
    <Edit title="Редактирование менеджера" saveButtonProps={saveButtonProps}>
      <Form {...formProps} layout="vertical">
        <Form.Item label="Логин" name="username">
          <Input />
        </Form.Item>
        <Form.Item label="ФИО" name="full_name">
          <Input />
        </Form.Item>
        <Form.Item label="Телефон" name="phone_number">
          <Input />
        </Form.Item>
        <Form.Item label="Тип" name="user_type">
          <Select options={userTypeOptions} />
        </Form.Item>
        <Form.Item label="Заведение" name="establishment">
          <Input />
        </Form.Item>
        <Form.Item label="Активен" name="is_active" valuePropName="checked">
          <Switch />
        </Form.Item>
      </Form>
      <SaveButton {...saveButtonProps}>Сохранить</SaveButton>
    </Edit>
  );
}

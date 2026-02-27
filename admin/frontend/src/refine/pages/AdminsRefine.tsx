import { Create, DeleteButton, Edit, EditButton, List, SaveButton, useForm, useTable } from "@refinedev/antd";
import { Form, Input, Select, Switch, Table } from "antd";

type AdminRecord = {
  id: number;
  username: string;
  email?: string | null;
  role: "superadmin" | "admin" | "manager";
  is_active: boolean;
  password?: string;
};

const roleOptions = [
  { label: "Суперадмин", value: "superadmin" },
  { label: "Админ", value: "admin" },
  { label: "Менеджер", value: "manager" },
];

export function AdminsList() {
  const { tableProps } = useTable<AdminRecord>({ resource: "admins" });

  return (
    <List title="Администраторы">
      <Table {...tableProps} rowKey="id" pagination={{ pageSize: 10, showSizeChanger: true }}>
        <Table.Column dataIndex="id" title="№" />
        <Table.Column dataIndex="username" title="Логин" />
        <Table.Column dataIndex="email" title="Почта" />
        <Table.Column<AdminRecord>
          dataIndex="role"
          title="Роль"
          render={(value) => roleOptions.find((item) => item.value === value)?.label ?? value}
        />
        <Table.Column<AdminRecord> dataIndex="is_active" title="Активен" render={(value) => (value ? "Да" : "Нет")} />
        <Table.Column<AdminRecord>
          title="Действия"
          render={(_, record) => (
            <>
              <EditButton hideText size="small" recordItemId={record.id} />
              <DeleteButton hideText size="small" recordItemId={record.id} />
            </>
          )}
        />
      </Table>
    </List>
  );
}

export function AdminsCreate() {
  const { formProps, saveButtonProps } = useForm<AdminRecord>({ resource: "admins", action: "create" });

  return (
    <Create title="Создание администратора" saveButtonProps={saveButtonProps}>
      <Form {...formProps} layout="vertical">
        <Form.Item label="Логин" name="username" rules={[{ required: true, message: "Введите логин" }]}>
          <Input placeholder="Например, admin" />
        </Form.Item>
        <Form.Item label="Почта" name="email" rules={[{ type: "email", message: "Некорректный email" }]}>
          <Input placeholder="admin@example.com" />
        </Form.Item>
        <Form.Item label="Пароль" name="password" rules={[{ required: true, min: 8, message: "Минимум 8 символов" }]}>
          <Input.Password />
        </Form.Item>
        <Form.Item label="Роль" name="role" initialValue="manager">
          <Select options={roleOptions} />
        </Form.Item>
      </Form>
      <SaveButton {...saveButtonProps}>Сохранить</SaveButton>
    </Create>
  );
}

export function AdminsEdit() {
  const { formProps, saveButtonProps } = useForm<AdminRecord>({ resource: "admins", action: "edit" });

  return (
    <Edit title="Редактирование администратора" saveButtonProps={saveButtonProps}>
      <Form {...formProps} layout="vertical">
        <Form.Item label="Почта" name="email" rules={[{ type: "email", message: "Некорректный email" }]}>
          <Input placeholder="admin@example.com" />
        </Form.Item>
        <Form.Item label="Роль" name="role">
          <Select options={roleOptions} />
        </Form.Item>
        <Form.Item label="Активен" name="is_active" valuePropName="checked">
          <Switch />
        </Form.Item>
        <Form.Item
          label="Новый пароль"
          name="password"
          extra="Оставьте пустым, если менять пароль не нужно"
          getValueFromEvent={(event) => {
            const value = event?.target?.value;
            return typeof value === "string" && value.trim() ? value : undefined;
          }}
        >
          <Input.Password />
        </Form.Item>
      </Form>
      <SaveButton {...saveButtonProps}>Сохранить</SaveButton>
    </Edit>
  );
}


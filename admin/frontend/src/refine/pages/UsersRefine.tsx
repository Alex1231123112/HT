import { Create, DeleteButton, Edit, EditButton, List, SaveButton, useForm, useTable } from "@refinedev/antd";
import { Table, Form, Input, Select, Switch, InputNumber, DatePicker } from "antd";
import dayjs, { type Dayjs } from "dayjs";

type UserRecord = {
  id: number;
  username: string | null;
  first_name?: string | null;
  last_name?: string | null;
  phone_number?: string | null;
  full_name?: string | null;
  birth_date?: string | null;
  position?: string | null;
  user_type: "horeca" | "retail";
  establishment: string;
  is_active?: boolean;
  registered_at?: string | null;
  last_activity?: string | null;
};

export function UsersList() {
  const { tableProps } = useTable<UserRecord>({ resource: "users" });

  return (
    <List title="Пользователи">
      <Table
        {...tableProps}
        rowKey={(record) => String(record.id)}
        pagination={{ pageSize: 10, showSizeChanger: true }}
      >
        <Table.Column dataIndex="id" title="№" width={80} />
        <Table.Column dataIndex="username" title="Логин" />
        <Table.Column dataIndex="phone_number" title="Телефон" />
        <Table.Column dataIndex="full_name" title="ФИО" />
        <Table.Column dataIndex="user_type" title="Тип" />
        <Table.Column dataIndex="establishment" title="Заведение" />
        <Table.Column dataIndex="position" title="Должность" />
        <Table.Column<UserRecord>
          dataIndex="birth_date"
          title="Дата рождения"
          render={(v) => (v ? dayjs(v).format("DD.MM.YYYY") : "—")}
        />
        <Table.Column<UserRecord>
          dataIndex="registered_at"
          title="Регистрация"
          render={(v) => (v ? dayjs(v).format("DD.MM.YYYY HH:mm") : "—")}
        />
        <Table.Column<UserRecord>
          dataIndex="is_active"
          title="Активен"
          render={(value) => (value ? "Да" : "Нет")}
        />
        <Table.Column<UserRecord>
          title="Действия"
          dataIndex="actions"
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

export function UsersCreate() {
  const { formProps, saveButtonProps } = useForm<UserRecord>({ resource: "users", action: "create" });

  return (
    <Create title="Создание пользователя" saveButtonProps={saveButtonProps}>
      <Form {...formProps} layout="vertical">
        <Form.Item label="ID" name="id" rules={[{ required: true }]}>
          <InputNumber style={{ width: "100%" }} />
        </Form.Item>
        <Form.Item label="Логин" name="username">
          <Input />
        </Form.Item>
        <Form.Item label="Имя" name="first_name">
          <Input />
        </Form.Item>
        <Form.Item label="Фамилия" name="last_name">
          <Input />
        </Form.Item>
        <Form.Item label="Телефон" name="phone_number">
          <Input placeholder="+7..." />
        </Form.Item>
        <Form.Item label="ФИО" name="full_name">
          <Input placeholder="Полное имя" />
        </Form.Item>
        <Form.Item
          label="Дата рождения"
          name="birth_date"
          getValueFromEvent={(d: Dayjs | null) => (d ? d.format("YYYY-MM-DD") : null)}
        >
          <DatePicker style={{ width: "100%" }} format="DD.MM.YYYY" />
        </Form.Item>
        <Form.Item label="Должность" name="position">
          <Input />
        </Form.Item>
        <Form.Item label="Тип пользователя" name="user_type" rules={[{ required: true }]}>
          <Select
            options={[
              { label: "HoReCa", value: "horeca" },
              { label: "Розница", value: "retail" },
            ]}
          />
        </Form.Item>
        <Form.Item label="Заведение" name="establishment" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="Активен" name="is_active" valuePropName="checked" initialValue>
          <Switch />
        </Form.Item>
      </Form>
      <SaveButton {...saveButtonProps}>Сохранить</SaveButton>
    </Create>
  );
}

export function UsersEdit() {
  const { formProps, saveButtonProps } = useForm<UserRecord>({ resource: "users", action: "edit" });

  return (
    <Edit title="Редактирование пользователя" saveButtonProps={saveButtonProps}>
      <Form {...formProps} layout="vertical">
        <Form.Item label="Логин" name="username">
          <Input />
        </Form.Item>
        <Form.Item label="Имя" name="first_name">
          <Input />
        </Form.Item>
        <Form.Item label="Фамилия" name="last_name">
          <Input />
        </Form.Item>
        <Form.Item label="Телефон" name="phone_number">
          <Input placeholder="+7..." />
        </Form.Item>
        <Form.Item label="ФИО" name="full_name">
          <Input placeholder="Полное имя" />
        </Form.Item>
        <Form.Item
          label="Дата рождения"
          name="birth_date"
          getValueProps={(v: string | null) => ({ value: v ? dayjs(v) : null })}
          getValueFromEvent={(d: Dayjs | null) => (d ? d.format("YYYY-MM-DD") : null)}
        >
          <DatePicker style={{ width: "100%" }} format="DD.MM.YYYY" />
        </Form.Item>
        <Form.Item label="Должность" name="position">
          <Input />
        </Form.Item>
        <Form.Item label="Тип пользователя" name="user_type">
          <Select
            options={[
              { label: "HoReCa", value: "horeca" },
              { label: "Розница", value: "retail" },
            ]}
          />
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


import { useList } from "@refinedev/core";
import { Create, DeleteButton, Edit, EditButton, List, useForm, useTable } from "@refinedev/antd";
import { useParams } from "react-router-dom";
import { Form, Input, Select, Switch, Table, Typography } from "antd";

type ManagerRecord = {
  id: number;
  full_name?: string | null;
  phone_number?: string | null;
  telegram_username?: string | null;
  telegram_user_id?: number | null;
  establishment: string;
  user_type?: string;
  is_active?: boolean;
  created_at?: string | null;
  updated_at?: string | null;
};

/** Преобразование строки "A, B" в массив для Select mode="multiple" и обратно. */
const establishmentToValue = (v: unknown): string[] =>
  typeof v === "string" ? v.split(/,\s*/).map((s) => s.trim()).filter(Boolean) : [];
const valueToEstablishment = (v: unknown): string =>
  Array.isArray(v) ? v.join(", ") : String(v ?? "");

export function ManagersList() {
  const { tableProps } = useTable<ManagerRecord>({ resource: "managers" });

  return (
    <List
      title="Менеджеры"
      description="Справочник контактов менеджеров (ФИО, телефон, Telegram, заведения). Отдельная таблица от пользователей бота."
      createButtonProps={{ size: "middle" }}
    >
      <Table
        {...tableProps}
        rowKey={(record) => String(record.id)}
        pagination={{ pageSize: 20, showSizeChanger: true }}
      >
        <Table.Column dataIndex="full_name" title="ФИО" render={(v) => v || "—"} />
        <Table.Column dataIndex="phone_number" title="Телефон" render={(v) => v || "—"} />
        <Table.Column<ManagerRecord>
          title="Telegram"
          key="telegram"
          render={(_, record) => {
            if (record.telegram_username) {
              return (
                <a href={`https://t.me/${record.telegram_username}`} target="_blank" rel="noopener noreferrer">
                  @{record.telegram_username}
                </a>
              );
            }
            if (record.telegram_user_id) {
              return <Typography.Text type="secondary">ID: {record.telegram_user_id}</Typography.Text>;
            }
            return "—";
          }}
        />
        <Table.Column dataIndex="establishment" title="Заведение" />
        <Table.Column<ManagerRecord>
          dataIndex="is_active"
          title="Активен"
          render={(v) => (v ? "Да" : "Нет")}
        />
        <Table.Column<ManagerRecord>
          title="Действия"
          width={120}
          render={(_, record) => (
            <>
              <EditButton hideText size="small" recordItemId={record.id} />
              <DeleteButton resource="managers" hideText size="small" recordItemId={record.id} />
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
  { label: "Все", value: "all" },
];

export function ManagersCreate() {
  const { formProps, saveButtonProps } = useForm<ManagerRecord>({ resource: "managers", action: "create" });
  const { result: establishmentsResult } = useList<{ id: number; name: string }>({ resource: "establishments" });
  const establishmentsList = establishmentsResult?.data ?? [];
  const establishmentOptions = establishmentsList.map((e) => ({ label: e.name, value: e.name }));

  return (
    <Create title="Новый менеджер" saveButtonProps={{ ...saveButtonProps, children: "Сохранить" }}>
      <Form {...formProps} layout="vertical">
        <Form.Item label="ФИО" name="full_name">
          <Input placeholder="Фамилия Имя Отчество" />
        </Form.Item>
        <Form.Item label="Телефон" name="phone_number">
          <Input placeholder="+7..." />
        </Form.Item>
        <Form.Item label="Telegram (username)" name="telegram_username">
          <Input placeholder="@username" />
        </Form.Item>
        <Form.Item label="Тип" name="user_type" rules={[{ required: true }]} initialValue="horeca">
          <Select options={userTypeOptions} />
        </Form.Item>
        <Form.Item
          label="Заведение"
          name="establishment"
          rules={[{ required: true, message: "Выберите хотя бы одно заведение" }]}
          getValueProps={(v) => ({ value: establishmentToValue(v) })}
          getValueFromEvent={(v) => valueToEstablishment(v)}
        >
          <Select mode="multiple" options={establishmentOptions} placeholder="Выберите заведения" allowClear />
        </Form.Item>
        <Form.Item label="Активен" name="is_active" valuePropName="checked" initialValue={true}>
          <Switch />
        </Form.Item>
      </Form>
    </Create>
  );
}

export function ManagersEdit() {
  const params = useParams<{ id: string }>();
  const id = params.id != null ? Number(params.id) : undefined;
  const { formProps, saveButtonProps } = useForm<ManagerRecord>({
    resource: "managers",
    action: "edit",
    id: id != null && !Number.isNaN(id) ? id : undefined,
  });
  const { result: establishmentsResult } = useList<{ id: number; name: string }>({ resource: "establishments" });
  const establishmentsList = establishmentsResult?.data ?? [];
  const establishmentOptions = establishmentsList.map((e) => ({ label: e.name, value: e.name }));

  return (
    <Edit title="Редактирование менеджера" saveButtonProps={{ ...saveButtonProps, children: "Сохранить" }}>
      <Form {...formProps} layout="vertical">
        <Form.Item label="ФИО" name="full_name">
          <Input />
        </Form.Item>
        <Form.Item label="Телефон" name="phone_number">
          <Input />
        </Form.Item>
        <Form.Item label="Telegram (username)" name="telegram_username">
          <Input placeholder="@username" />
        </Form.Item>
        <Form.Item label="Тип" name="user_type">
          <Select options={userTypeOptions} />
        </Form.Item>
        <Form.Item
          label="Заведение"
          name="establishment"
          getValueProps={(v) => ({ value: establishmentToValue(v) })}
          getValueFromEvent={(v) => valueToEstablishment(v)}
        >
          <Select mode="multiple" options={establishmentOptions} placeholder="Выберите заведения" allowClear />
        </Form.Item>
        <Form.Item label="Активен" name="is_active" valuePropName="checked">
          <Switch />
        </Form.Item>
      </Form>
    </Edit>
  );
}

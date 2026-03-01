import { Create, DeleteButton, Edit, EditButton, List, SaveButton, useForm, useTable } from "@refinedev/antd";
import { Form, Input, Select, Table, Tag } from "antd";

type EstablishmentRecord = {
  id: number;
  name: string;
  user_type: string;
  user_count: number;
};

const typeLabels: Record<string, string> = {
  horeca: "HoReCa",
  retail: "Розница",
  all: "Все",
};

const typeOptions = [
  { label: "HoReCa", value: "horeca" },
  { label: "Розница", value: "retail" },
  { label: "Все", value: "all" },
];

export function EstablishmentsList() {
  const { tableProps } = useTable<EstablishmentRecord>({ resource: "establishments" });

  return (
    <List
      title="Заведения"
      description="Справочник заведений с типом (HoReCa/Розница). Указано количество контактов в боте по каждому заведению."
      createButtonProps={{ size: "middle" }}
    >
      <Table {...tableProps} rowKey="id" pagination={{ pageSize: 20, showSizeChanger: true }}>
        <Table.Column dataIndex="name" title="Заведение" />
        <Table.Column<EstablishmentRecord>
          dataIndex="user_type"
          title="Тип"
          render={(user_type) => (
            <Tag color={user_type === "horeca" ? "blue" : user_type === "retail" ? "green" : "default"}>
              {typeLabels[user_type] ?? user_type}
            </Tag>
          )}
        />
        <Table.Column dataIndex="user_count" title="Контактов" width={100} />
        <Table.Column<EstablishmentRecord>
          title="Действия"
          width={120}
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

export function EstablishmentsCreate() {
  const { formProps, saveButtonProps } = useForm<EstablishmentRecord>({
    resource: "establishments",
    action: "create",
  });

  return (
    <Create title="Новое заведение" saveButtonProps={saveButtonProps}>
      <Form {...formProps} layout="vertical">
        <Form.Item label="Название" name="name" rules={[{ required: true }]}>
          <Input placeholder="Название заведения" />
        </Form.Item>
        <Form.Item label="Тип" name="user_type" rules={[{ required: true }]}>
          <Select options={typeOptions} />
        </Form.Item>
      </Form>
      <SaveButton {...saveButtonProps}>Сохранить</SaveButton>
    </Create>
  );
}

export function EstablishmentsEdit() {
  const { formProps, saveButtonProps } = useForm<EstablishmentRecord>({
    resource: "establishments",
    action: "edit",
  });

  return (
    <Edit title="Редактирование заведения" saveButtonProps={saveButtonProps}>
      <Form {...formProps} layout="vertical">
        <Form.Item label="Название" name="name" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="Тип" name="user_type" rules={[{ required: true }]}>
          <Select options={typeOptions} />
        </Form.Item>
      </Form>
      <SaveButton {...saveButtonProps}>Сохранить</SaveButton>
    </Edit>
  );
}

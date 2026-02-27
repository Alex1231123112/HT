import { Create, DeleteButton, Edit, EditButton, List, SaveButton, useForm, useTable } from "@refinedev/antd";
import { Form, Input, Select, Switch, Table } from "antd";

type ContentRecord = {
  id: number;
  title: string;
  description: string;
  image_url?: string | null;
  user_type: "all" | "horeca" | "retail";
  is_active: boolean;
  published_at?: string | null;
};

const audienceOptions = [
  { label: "Все", value: "all" },
  { label: "HoReCa", value: "horeca" },
  { label: "Розница", value: "retail" },
];

export function ContentList({ resource }: { resource: "promotions" | "news" | "deliveries" }) {
  const { tableProps } = useTable<ContentRecord>({ resource });

  return (
    <List title="Контент">
      <Table {...tableProps} rowKey="id" pagination={{ pageSize: 10, showSizeChanger: true }}>
        <Table.Column dataIndex="id" title="№" />
        <Table.Column dataIndex="title" title="Заголовок" />
        <Table.Column dataIndex="user_type" title="Аудитория" />
        <Table.Column<ContentRecord> dataIndex="is_active" title="Активен" render={(value) => (value ? "Да" : "Нет")} />
        <Table.Column<ContentRecord>
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

export function ContentCreate({ resource }: { resource: "promotions" | "news" | "deliveries" }) {
  const { formProps, saveButtonProps } = useForm<ContentRecord>({ resource, action: "create" });

  return (
    <Create title="Создание контента" saveButtonProps={saveButtonProps}>
      <Form {...formProps} layout="vertical">
        <Form.Item label="Заголовок" name="title" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="Описание" name="description">
          <Input.TextArea />
        </Form.Item>
        <Form.Item label="Ссылка на медиа" name="image_url">
          <Input />
        </Form.Item>
        <Form.Item label="Аудитория" name="user_type" initialValue="all">
          <Select options={audienceOptions} />
        </Form.Item>
        <Form.Item label="Активен" name="is_active" valuePropName="checked" initialValue>
          <Switch />
        </Form.Item>
      </Form>
      <SaveButton {...saveButtonProps}>Сохранить</SaveButton>
    </Create>
  );
}

export function ContentEdit({ resource }: { resource: "promotions" | "news" | "deliveries" }) {
  const { formProps, saveButtonProps } = useForm<ContentRecord>({ resource, action: "edit" });

  return (
    <Edit title="Редактирование контента" saveButtonProps={saveButtonProps}>
      <Form {...formProps} layout="vertical">
        <Form.Item label="Заголовок" name="title" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="Описание" name="description">
          <Input.TextArea />
        </Form.Item>
        <Form.Item label="Ссылка на медиа" name="image_url">
          <Input />
        </Form.Item>
        <Form.Item label="Аудитория" name="user_type">
          <Select options={audienceOptions} />
        </Form.Item>
        <Form.Item label="Активен" name="is_active" valuePropName="checked">
          <Switch />
        </Form.Item>
      </Form>
      <SaveButton {...saveButtonProps}>Сохранить</SaveButton>
    </Edit>
  );
}


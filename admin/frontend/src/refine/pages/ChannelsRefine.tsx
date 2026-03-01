import { Create, DeleteButton, Edit, EditButton, List, SaveButton, useForm, useTable } from "@refinedev/antd";
import { Form, Input, Select, Switch, Table } from "antd";

type ChannelRecord = {
  id: number;
  name: string;
  channel_type: "bot" | "telegram_channel";
  telegram_ref?: string | null;
  is_active: boolean;
  created_at?: string;
};

const channelTypeOptions = [
  { label: "Бот", value: "bot" },
  { label: "Telegram-канал", value: "telegram_channel" },
];

export function ChannelsList() {
  const { tableProps } = useTable<ChannelRecord>({ resource: "channels" });

  return (
    <List
      title="Каналы рассылки"
      description="Список каналов, в которые можно отправить контент: бот (подписчики) или Telegram-канал (@username или chat_id)."
    >
      <Table {...tableProps} rowKey="id" pagination={{ pageSize: 20, showSizeChanger: true }}>
        <Table.Column dataIndex="id" title="№" width={60} />
        <Table.Column dataIndex="name" title="Название" />
        <Table.Column<ChannelRecord>
          dataIndex="channel_type"
          title="Тип"
          render={(t) => (t === "bot" ? "Бот" : "Telegram-канал")}
        />
        <Table.Column dataIndex="telegram_ref" title="Ссылка/chat_id" ellipsis />
        <Table.Column<ChannelRecord>
          dataIndex="is_active"
          title="Активен"
          render={(v) => (v ? "Да" : "Нет")}
          width={80}
        />
        <Table.Column<ChannelRecord>
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

export function ChannelsCreate() {
  const { formProps, saveButtonProps } = useForm<ChannelRecord>({
    resource: "channels",
    action: "create",
    defaultValues: { is_active: true, channel_type: "bot" },
  });

  return (
    <Create title="Добавить канал рассылки" saveButtonProps={saveButtonProps}>
      <Form {...formProps} layout="vertical">
        <Form.Item label="Название" name="name" rules={[{ required: true }]}>
          <Input placeholder="Например: Основной бот" />
        </Form.Item>
        <Form.Item label="Тип" name="channel_type" rules={[{ required: true }]}>
          <Select options={channelTypeOptions} />
        </Form.Item>
        <Form.Item
          label="Ссылка на канал (username или chat_id)"
          name="telegram_ref"
          help="Для Telegram-канала укажите @username или числовой chat_id."
        >
          <Input placeholder="@channel или -1001234567890" />
        </Form.Item>
        <Form.Item label="Активен" name="is_active" valuePropName="checked">
          <Switch />
        </Form.Item>
      </Form>
    </Create>
  );
}

export function ChannelsEdit() {
  const { formProps, saveButtonProps } = useForm<ChannelRecord>({ resource: "channels", action: "edit" });

  return (
    <Edit title="Редактировать канал" saveButtonProps={saveButtonProps}>
      <Form {...formProps} layout="vertical">
        <Form.Item label="Название" name="name" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="Тип" name="channel_type" rules={[{ required: true }]}>
          <Select options={channelTypeOptions} />
        </Form.Item>
        <Form.Item label="Ссылка на канал (username или chat_id)" name="telegram_ref">
          <Input placeholder="@channel или -1001234567890" />
        </Form.Item>
        <Form.Item label="Активен" name="is_active" valuePropName="checked">
          <Switch />
        </Form.Item>
      </Form>
    </Edit>
  );
}

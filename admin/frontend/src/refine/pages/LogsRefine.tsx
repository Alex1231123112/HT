import { List, useTable } from "@refinedev/antd";
import { Table, Tabs } from "antd";

type LogRecord = {
  id: number;
  admin_id?: number;
  action: string;
  details?: string;
  created_at: string;
};

type DeliveryLogRecord = {
  id: number;
  plan_id: number;
  plan_title: string;
  channel_type: string;
  target: string;
  success: boolean;
  error_message?: string;
  admin_id?: number;
  created_at: string;
};

function ActivityLogsTable() {
  const { tableProps } = useTable<LogRecord>({ resource: "logs" });
  return (
    <Table {...tableProps} rowKey="id" pagination={{ pageSize: 20, showSizeChanger: true }}>
      <Table.Column dataIndex="id" title="№" width={70} />
      <Table.Column dataIndex="admin_id" title="Админ" width={80} />
      <Table.Column dataIndex="action" title="Действие" />
      <Table.Column dataIndex="details" title="Детали" ellipsis />
      <Table.Column dataIndex="created_at" title="Создано" width={180} />
    </Table>
  );
}

function DeliveryLogsTable() {
  const { tableProps } = useTable<DeliveryLogRecord>({ resource: "delivery_logs" });
  return (
    <Table {...tableProps} rowKey="id" pagination={{ pageSize: 20, showSizeChanger: true }}>
      <Table.Column dataIndex="id" title="№" width={70} />
      <Table.Column dataIndex="plan_id" title="План №" width={80} />
      <Table.Column dataIndex="plan_title" title="План" ellipsis />
      <Table.Column
        dataIndex="channel_type"
        title="Канал"
        width={120}
        render={(v: string) => (v === "bot" ? "Бот" : "Telegram-канал")}
      />
      <Table.Column dataIndex="target" title="Получатель" width={140} />
      <Table.Column
        dataIndex="success"
        title="Успех"
        width={80}
        render={(v: boolean) => (v ? "✓" : "✗")}
      />
      <Table.Column dataIndex="error_message" title="Ошибка" ellipsis />
      <Table.Column dataIndex="created_at" title="Создано" width={180} />
    </Table>
  );
}

export function LogsList() {
  return (
    <List title="Логи">
      <Tabs
        defaultActiveKey="activity"
        items={[
          { key: "activity", label: "Действия админов", children: <ActivityLogsTable /> },
          { key: "delivery", label: "Отправки в Telegram", children: <DeliveryLogsTable /> },
        ]}
      />
    </List>
  );
}


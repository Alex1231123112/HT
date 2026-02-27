import { List, useTable } from "@refinedev/antd";
import { Table } from "antd";

type LogRecord = {
  id: number;
  admin_id?: number;
  action: string;
  details?: string;
  created_at: string;
};

export function LogsList() {
  const { tableProps } = useTable<LogRecord>({ resource: "logs" });

  return (
    <List title="Журнал действий">
      <Table {...tableProps} rowKey="id" pagination={{ pageSize: 20, showSizeChanger: true }}>
        <Table.Column dataIndex="id" title="№" />
        <Table.Column dataIndex="admin_id" title="Админ" />
        <Table.Column dataIndex="action" title="Действие" />
        <Table.Column dataIndex="details" title="Детали" />
        <Table.Column dataIndex="created_at" title="Создано" />
      </Table>
    </List>
  );
}


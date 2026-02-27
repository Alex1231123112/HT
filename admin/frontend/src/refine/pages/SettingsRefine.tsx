import { Edit, SaveButton, useForm, useTable } from "@refinedev/antd";
import { Form, Input, Table } from "antd";
import { useMemo } from "react";

type SettingRecord = { id: string; key: string; value: string };

export function SettingsList() {
  const { tableProps } = useTable<SettingRecord>({ resource: "settings" });

  return (
    <Table {...tableProps} rowKey="id" pagination={false}>
      <Table.Column dataIndex="key" title="Ключ" />
      <Table.Column dataIndex="value" title="Значение" />
    </Table>
  );
}

export function SettingsEdit() {
  const { tableProps } = useTable<SettingRecord>({ resource: "settings" });
  const firstKey = useMemo(() => (tableProps?.dataSource?.[0] as SettingRecord | undefined)?.key, [tableProps.dataSource]);
  const { formProps, saveButtonProps } = useForm<SettingRecord>({
    resource: "settings",
    action: "edit",
    id: firstKey,
  });

  return (
    <Edit title="Системные настройки" saveButtonProps={saveButtonProps}>
      <SettingsList />
      <Form {...formProps} layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item label="Ключ" name="key">
          <Input />
        </Form.Item>
        <Form.Item label="Значение" name="value">
          <Input.TextArea autoSize={{ minRows: 3, maxRows: 8 }} />
        </Form.Item>
      </Form>
      <SaveButton {...saveButtonProps}>Сохранить</SaveButton>
    </Edit>
  );
}


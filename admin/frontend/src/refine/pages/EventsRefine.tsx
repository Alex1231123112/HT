import { Create, DeleteButton, Edit, EditButton, List, SaveButton, useForm, useTable } from "@refinedev/antd";
import { Button, DatePicker, Drawer, Form, Input, InputNumber, message, Select, Switch, Table } from "antd";
import type { UploadProps } from "antd";
import { InboxOutlined, TeamOutlined } from "@ant-design/icons";
import Dragger from "antd/es/upload/Dragger";
import { getApiUrl, uploadContentFile } from "../providers";
import React, { useState } from "react";
import dayjs, { type Dayjs } from "dayjs";

const MAX_SIZE_MB = 5;

const audienceOptions = [
  { label: "Все", value: "all" },
  { label: "HoReCa", value: "horeca" },
  { label: "Розница", value: "retail" },
];

type EventRecord = {
  id: number;
  title: string;
  description: string;
  image_url?: string | null;
  user_type: "all" | "horeca" | "retail";
  event_date: string;
  location: string;
  is_active: boolean;
  max_places?: number | null;
  created_at: string;
  registered_count: number;
};

type RegistrationRecord = {
  id: number;
  event_id: number;
  user_id: number;
  registered_at: string;
  user_username?: string | null;
  user_full_name?: string | null;
  user_phone?: string | null;
  user_establishment?: string | null;
};

function MediaUploadField() {
  const form = Form.useFormInstance();
  const uploadProps: UploadProps = {
    name: "file",
    multiple: false,
    maxCount: 1,
    showUploadList: false,
    beforeUpload: async (file: File) => {
      if (file.size > MAX_SIZE_MB * 1024 * 1024) {
        message.error(`Файл не больше ${MAX_SIZE_MB} МБ`);
        return false;
      }
      try {
        const { url } = await uploadContentFile(file);
        form?.setFieldValue("image_url", url);
        message.success("Файл загружен");
      } catch (e) {
        message.error(e instanceof Error ? e.message : "Ошибка загрузки");
      }
      return false;
    },
  };
  return (
    <Dragger {...uploadProps}>
      <p className="ant-upload-drag-icon">
        <InboxOutlined style={{ fontSize: 48, color: "#1890ff" }} />
      </p>
      <p className="ant-upload-text">Нажмите или перетащите файл сюда</p>
      <p className="ant-upload-hint">Не более {MAX_SIZE_MB} МБ. Ссылка подставится в поле ниже.</p>
    </Dragger>
  );
}

function RegistrationsDrawer({
  eventId,
  eventTitle,
  open,
  onClose,
}: {
  eventId: number;
  eventTitle: string;
  open: boolean;
  onClose: () => void;
}) {
  const token = typeof localStorage !== "undefined" ? localStorage.getItem("token") ?? "" : "";
  const [data, setData] = useState<RegistrationRecord[]>([]);
  const [loading, setLoading] = useState(false);

  React.useEffect(() => {
    if (!open || !eventId) return;
    setLoading(true);
    fetch(`${getApiUrl()}/events/${eventId}/registrations`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((r) => r.json())
      .then((list: RegistrationRecord[]) => setData(Array.isArray(list) ? list : []))
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, [open, eventId, token]);

  return (
    <Drawer
      title={`Записаны на «${eventTitle}»`}
      open={open}
      onClose={onClose}
      width={520}
    >
      {loading ? (
        <p>Загрузка…</p>
      ) : data.length === 0 ? (
        <p>Пока никого нет.</p>
      ) : (
        <Table
          dataSource={data}
          rowKey="id"
          size="small"
          pagination={false}
          columns={[
            { dataIndex: "user_full_name", title: "Имя", render: (v: string) => v || "—" },
            { dataIndex: "user_username", title: "Username", render: (v: string) => v || "—" },
            { dataIndex: "user_phone", title: "Телефон", render: (v: string) => v || "—" },
            { dataIndex: "user_establishment", title: "Заведение", render: (v: string) => v || "—" },
            {
              dataIndex: "registered_at",
              title: "Дата записи",
              render: (v: string) => (v ? dayjs(v).format("DD.MM.YYYY HH:mm") : "—"),
            },
          ]}
        />
      )}
    </Drawer>
  );
}

export function EventsList() {
  const [regDrawer, setRegDrawer] = useState<{ id: number; title: string } | null>(null);
  const { tableProps } = useTable<EventRecord>({ resource: "events" });

  return (
    <>
      <List
        title="Мероприятия"
        description="Управление мероприятиями и лимитом мест. Регистрации пользователей бота отображаются в списке «Записано»."
      >
        <Table {...tableProps} rowKey="id" pagination={{ pageSize: 15, showSizeChanger: true }}>
          <Table.Column dataIndex="id" title="№" width={50} />
          <Table.Column dataIndex="title" title="Название" ellipsis />
          <Table.Column<EventRecord>
            dataIndex="event_date"
            title="Дата"
            render={(v) => (v ? dayjs(v).format("DD.MM.YYYY HH:mm") : "—")}
            width={140}
          />
          <Table.Column dataIndex="location" title="Место" ellipsis />
          <Table.Column<EventRecord>
            dataIndex="max_places"
            title="Лимит мест"
            render={(v) => (v == null ? "—" : v)}
            width={100}
          />
          <Table.Column<EventRecord>
            dataIndex="registered_count"
            title="Записано"
            width={100}
            render={(_, record) => (
              <Button
                type="link"
                size="small"
                icon={<TeamOutlined />}
                onClick={() => setRegDrawer({ id: record.id, title: record.title })}
              >
                {record.registered_count}
              </Button>
            )}
          />
          <Table.Column<EventRecord>
            dataIndex="is_active"
            title="Активен"
            width={80}
            render={(v) => (v ? "Да" : "Нет")}
          />
          <Table.Column<EventRecord>
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
      {regDrawer && (
        <RegistrationsDrawer
          eventId={regDrawer.id}
          eventTitle={regDrawer.title}
          open={!!regDrawer}
          onClose={() => setRegDrawer(null)}
        />
      )}
    </>
  );
}

export function EventsCreate() {
  const { formProps, saveButtonProps } = useForm<EventRecord>({
    resource: "events",
    action: "create",
    defaultValues: { is_active: true, user_type: "all", description: "", location: "" },
  });

  return (
    <Create title="Новое мероприятие" saveButtonProps={saveButtonProps}>
      <Form {...formProps} layout="vertical">
        <Form.Item label="Название" name="title" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="Описание" name="description">
          <Input.TextArea rows={3} />
        </Form.Item>
        <Form.Item label="Медиа" help="Загрузите файл или вставьте ссылку ниже.">
          <MediaUploadField />
        </Form.Item>
        <Form.Item label="Ссылка на медиа" name="image_url">
          <Input placeholder="URL или после загрузки" />
        </Form.Item>
        <Form.Item label="Аудитория" name="user_type" rules={[{ required: true }]}>
          <Select options={audienceOptions} />
        </Form.Item>
        <Form.Item
          label="Дата и время"
          name="event_date"
          rules={[{ required: true }]}
          getValueProps={(v: string) => ({ value: v ? dayjs(v) : null })}
          getValueFromEvent={(d: Dayjs | null) => (d ? d.toISOString() : null)}
        >
          <DatePicker showTime format="DD.MM.YYYY HH:mm" style={{ width: "100%" }} />
        </Form.Item>
        <Form.Item label="Место проведения" name="location">
          <Input placeholder="Адрес или название площадки" />
        </Form.Item>
        <Form.Item label="Лимит мест" name="max_places" help="Оставьте пустым, если мест без ограничений.">
          <InputNumber min={1} placeholder="Не ограничено" style={{ width: "100%" }} />
        </Form.Item>
        <Form.Item label="Активен (виден в боте)" name="is_active" valuePropName="checked">
          <Switch />
        </Form.Item>
      </Form>
    </Create>
  );
}

export function EventsEdit() {
  const { formProps, saveButtonProps } = useForm<EventRecord>({ resource: "events", action: "edit" });

  return (
    <Edit title="Редактирование мероприятия" saveButtonProps={saveButtonProps}>
      <Form {...formProps} layout="vertical">
        <Form.Item label="Название" name="title" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="Описание" name="description">
          <Input.TextArea rows={3} />
        </Form.Item>
        <Form.Item label="Медиа">
          <MediaUploadField />
        </Form.Item>
        <Form.Item label="Ссылка на медиа" name="image_url">
          <Input />
        </Form.Item>
        <Form.Item label="Аудитория" name="user_type" rules={[{ required: true }]}>
          <Select options={audienceOptions} />
        </Form.Item>
        <Form.Item
          label="Дата и время"
          name="event_date"
          rules={[{ required: true }]}
          getValueProps={(v: string) => ({ value: v ? dayjs(v) : null })}
          getValueFromEvent={(d: Dayjs | null) => (d ? d.toISOString() : null)}
        >
          <DatePicker showTime format="DD.MM.YYYY HH:mm" style={{ width: "100%" }} />
        </Form.Item>
        <Form.Item label="Место проведения" name="location">
          <Input />
        </Form.Item>
        <Form.Item label="Лимит мест" name="max_places">
          <InputNumber min={1} placeholder="Не ограничено" style={{ width: "100%" }} />
        </Form.Item>
        <Form.Item label="Активен" name="is_active" valuePropName="checked">
          <Switch />
        </Form.Item>
      </Form>
    </Edit>
  );
}

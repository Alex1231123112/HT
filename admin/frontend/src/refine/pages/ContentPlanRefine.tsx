import { useList } from "@refinedev/core";
import { Create, DeleteButton, Edit, EditButton, List, SaveButton, useForm, useTable } from "@refinedev/antd";
import { DatePicker, Form, Input, Select, Table } from "antd";
import type { Dayjs } from "dayjs";
import dayjs from "dayjs";

type ContentPlanRecord = {
  id: number;
  title: string;
  content_type: "promotion" | "news" | "delivery" | "event" | "custom";
  content_id?: number | null;
  custom_title?: string | null;
  custom_description?: string | null;
  custom_media_url?: string | null;
  scheduled_at?: string | null;
  status: "draft" | "scheduled" | "sent" | "cancelled";
  sent_at?: string | null;
  created_at: string;
  channel_ids: number[];
};

const contentTypeOptions = [
  { label: "Акция", value: "promotion" },
  { label: "Новость", value: "news" },
  { label: "Поставка", value: "delivery" },
  { label: "Мероприятие", value: "event" },
  { label: "Свой контент", value: "custom" },
];

const statusOptions = [
  { label: "Черновик", value: "draft" },
  { label: "Запланировано", value: "scheduled" },
  { label: "Отправлено", value: "sent" },
  { label: "Отменено", value: "cancelled" },
];

const resourceByContentType: Record<string, string> = {
  promotion: "promotions",
  news: "news",
  delivery: "deliveries",
  event: "events",
};

export function ContentPlanList() {
  const { tableProps } = useTable<ContentPlanRecord>({ resource: "content_plan" });
  const { data: channelsData } = useList<{ id: number; name: string }>({ resource: "channels" });
  const channels = channelsData?.data ?? [];

  return (
    <List
      title="Контент план"
      description="Планирование рассылки контента в бот и в Telegram-каналы. Выберите тип контента, дату отправки и каналы."
    >
      <Table {...tableProps} rowKey="id" pagination={{ pageSize: 15, showSizeChanger: true }}>
        <Table.Column dataIndex="id" title="№" width={60} />
        <Table.Column dataIndex="title" title="Название" ellipsis />
        <Table.Column<ContentPlanRecord>
          dataIndex="content_type"
          title="Тип контента"
          render={(t) => contentTypeOptions.find((o) => o.value === t)?.label ?? t}
        />
        <Table.Column<ContentPlanRecord>
          dataIndex="status"
          title="Статус"
          render={(s) => statusOptions.find((o) => o.value === s)?.label ?? s}
          width={120}
        />
        <Table.Column<ContentPlanRecord>
          dataIndex="scheduled_at"
          title="Запланировано"
          render={(v) => (v ? dayjs(v).format("DD.MM.YYYY HH:mm") : "—")}
          width={140}
        />
        <Table.Column<ContentPlanRecord>
          dataIndex="channel_ids"
          title="Каналы"
          render={(ids: number[]) => {
            if (!ids?.length) return "—";
            const names = ids.map((id) => channels.find((c) => c.id === id)?.name ?? id).join(", ");
            return names.length > 40 ? `${names.slice(0, 40)}…` : names;
          }}
        />
        <Table.Column<ContentPlanRecord>
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

function ContentPlanForm({ isEdit = false }: { isEdit?: boolean }) {
  const form = Form.useFormInstance();
  const contentType = Form.useWatch("content_type", form);

  const { data: channelsData } = useList<{ id: number; name: string }>({ resource: "channels" });
  const { data: promotionsData } = useList<{ id: number; title: string }>({ resource: "promotions" });
  const { data: newsData } = useList<{ id: number; title: string }>({ resource: "news" });
  const { data: deliveriesData } = useList<{ id: number; title: string }>({ resource: "deliveries" });
  const { data: eventsData } = useList<{ id: number; title: string }>({ resource: "events" });

  const channels = channelsData?.data ?? [];
  const promotions = promotionsData?.data ?? [];
  const news = newsData?.data ?? [];
  const deliveries = deliveriesData?.data ?? [];
  const events = eventsData?.data ?? [];

  const contentOptions =
    contentType === "promotion"
      ? promotions.map((p) => ({ label: p.title, value: p.id }))
      : contentType === "news"
        ? news.map((n) => ({ label: n.title, value: n.id }))
        : contentType === "delivery"
          ? deliveries.map((d) => ({ label: d.title, value: d.id }))
          : contentType === "event"
            ? events.map((e) => ({ label: e.title, value: e.id }))
            : [];

  const channelOptions = channels.map((c) => ({ label: c.name, value: c.id }));

  return (
    <>
      <Form.Item label="Название плана" name="title" rules={[{ required: true }]}>
        <Input placeholder="Например: Анонс акции на выходные" />
      </Form.Item>
      <Form.Item label="Тип контента" name="content_type" rules={[{ required: true }]}>
        <Select
          options={contentTypeOptions}
          onChange={() => {
            form?.setFieldValue("content_id", undefined);
            form?.setFieldValue("custom_title", undefined);
            form?.setFieldValue("custom_description", undefined);
            form?.setFieldValue("custom_media_url", undefined);
          }}
        />
      </Form.Item>
      {contentType === "custom" ? (
        <>
          <Form.Item label="Заголовок" name="custom_title">
            <Input />
          </Form.Item>
          <Form.Item label="Описание" name="custom_description">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item label="Ссылка на медиа" name="custom_media_url">
            <Input placeholder="URL картинки или видео" />
          </Form.Item>
        </>
      ) : contentType && contentOptions.length > 0 ? (
        <Form.Item label="Выбор контента" name="content_id">
          <Select allowClear options={contentOptions} placeholder="Выберите запись" />
        </Form.Item>
      ) : null}
      <Form.Item
        label="Дата и время отправки"
        name="scheduled_at"
        getValueProps={(v: string | null) => ({ value: v ? dayjs(v) : null })}
        normalize={(v: Dayjs | null) => (v ? v.toISOString() : null)}
      >
        <DatePicker showTime format="DD.MM.YYYY HH:mm" style={{ width: "100%" }} />
      </Form.Item>
      {isEdit && (
        <Form.Item label="Статус" name="status">
          <Select options={statusOptions} />
        </Form.Item>
      )}
      <Form.Item label="Каналы рассылки" name="channel_ids">
        <Select mode="multiple" allowClear options={channelOptions} placeholder="Выберите каналы" />
      </Form.Item>
    </>
  );
}

export function ContentPlanCreate() {
  const { formProps, saveButtonProps } = useForm<ContentPlanRecord>({
    resource: "content_plan",
    action: "create",
    defaultValues: { status: "draft", channel_ids: [] },
  });

  return (
    <Create title="Новая запись в контент плане" saveButtonProps={saveButtonProps}>
      <Form {...formProps} layout="vertical">
        <ContentPlanForm />
      </Form>
    </Create>
  );
}

export function ContentPlanEdit() {
  const { formProps, saveButtonProps } = useForm<ContentPlanRecord>({
    resource: "content_plan",
    action: "edit",
  });

  return (
    <Edit title="Редактирование контент плана" saveButtonProps={saveButtonProps}>
      <Form {...formProps} layout="vertical">
        <ContentPlanForm isEdit />
      </Form>
    </Edit>
  );
}

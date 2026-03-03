import { useCustomMutation, useInvalidate, useList } from "@refinedev/core";
import { Create, DeleteButton, Edit, EditButton, List, useForm, useTable } from "@refinedev/antd";
import { Button, Card, DatePicker, Form, Input, message, Select, Space, Table } from "antd";
import type { Dayjs } from "dayjs";
import dayjs from "dayjs";
import { CustomContentBlock } from "../components/PublicationEditor";

type ContentPlanItemRecord = {
  id?: number;
  plan_id?: number;
  sort_order?: number;
  content_type: "promotion" | "news" | "delivery" | "event" | "custom";
  content_id?: number | null;
  custom_title?: string | null;
  custom_description?: string | null;
  custom_media_url?: string | null;
};

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
  items?: ContentPlanItemRecord[];
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
  const { result: channelsResult } = useList<{ id: number; name: string }>({ resource: "channels" });
  const channels = channelsResult?.data ?? [];
  const invalidate = useInvalidate();
  const { mutate: sendPlan, isPending: sendPending } = useCustomMutation<{
    message?: string;
    data?: { sent_bot?: number; sent_channel?: number; errors?: string[]; hint?: string; channels_count?: number };
  }>();

  const handleSend = (record: ContentPlanRecord) => {
    if (record.status === "sent") {
      message.info("Уже отправлено.");
      return;
    }
    sendPlan(
      {
        url: `/content-plan/${record.id}/send`,
        method: "post",
        values: {},
      },
      {
        onSuccess: (res) => {
          const data = res?.data ?? {};
          const sentBot = data.sent_bot ?? 0;
          const sentChannel = data.sent_channel ?? 0;
          const errs = data.errors ?? [];
          const channelsCount = data.channels_count ?? 0;
          invalidate({ resource: "content_plan", invalidates: ["list"] });
          if (sentBot + sentChannel === 0) {
            const hint = data.hint ?? "Отправлено 0 сообщений. Проверьте каналы, пользователей и BOT_TOKEN.";
            message.warning(`Привязано каналов: ${channelsCount}. ${hint}${errs.length ? ` Ошибки: ${errs.join("; ")}` : ""}`, 12);
          } else {
            message.success(`Отправлено: в бот — ${sentBot}, в канал — ${sentChannel}.${errs.length ? ` Ошибки: ${errs.join("; ")}` : ""}`);
          }
        },
        onError: (e) => {
          message.error(e?.message ?? "Ошибка отправки");
        },
      }
    );
  };

  return (
    <List
      title="Контент план"
      description="Планирование рассылки контента в бот и в Telegram-каналы. Выберите тип контента, дату отправки и каналы. Нажмите «Отправить», чтобы отправить запись в привязанные каналы."
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
          dataIndex="items"
          title="Сообщений"
          width={100}
          render={(items: ContentPlanItemRecord[] | undefined) => (items?.length ? items.length : "1")}
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
          width={180}
          render={(_, record) => (
            <>
              {record.status !== "sent" && (
                <Button
                  type="primary"
                  size="small"
                  loading={sendPending}
                  onClick={() => handleSend(record)}
                  style={{ marginRight: 8 }}
                >
                  Отправить
                </Button>
              )}
              <EditButton hideText size="small" recordItemId={record.id} />
              <DeleteButton hideText size="small" recordItemId={record.id} />
            </>
          )}
        />
      </Table>
    </List>
  );
}

function OneMessageFields({
  namePath,
  contentType,
  contentOptions,
  onContentTypeChange,
  previewTitle,
  previewDescription,
  previewMediaUrl,
}: {
  namePath: (string | number)[];
  contentType: string;
  contentOptions: { label: string; value: number }[];
  onContentTypeChange: () => void;
  previewTitle?: string | null;
  previewDescription?: string | null;
  previewMediaUrl?: string | null;
}) {
  const form = Form.useFormInstance();

  return (
    <>
      <Form.Item name={[...namePath, "content_type"]} label="Раздел" rules={[{ required: true }]}>
        <Select options={contentTypeOptions} onChange={onContentTypeChange} placeholder="Из какого раздела выбрать" />
      </Form.Item>
      {contentType === "custom" ? (
        <CustomContentBlock
          namePath={namePath}
          form={form}
          previewTitle={previewTitle}
          previewDescription={previewDescription}
          previewMediaUrl={previewMediaUrl}
        />
      ) : contentType && contentOptions.length > 0 ? (
        <Form.Item
          name={[...namePath, "content_id"]}
          label="Что отправить"
          rules={[{ required: true, message: "Выберите запись из каталога" }]}
        >
          <Select allowClear options={contentOptions} placeholder="Выберите запись из каталога" />
        </Form.Item>
      ) : contentType && contentType !== "custom" ? (
        <Form.Item label="Что отправить" extra="В этом разделе пока нет записей. Создайте их в соответствующем разделе меню.">
          <Select disabled placeholder="Нет записей" options={[]} />
        </Form.Item>
      ) : null}
    </>
  );
}

function ContentPlanForm({ isEdit = false }: { isEdit?: boolean }) {
  const form = Form.useFormInstance();
  const planContentType = Form.useWatch("content_type", form);
  debugger;
  const items = Form.useWatch("items", form) ?? [];
  const planCustomTitle = Form.useWatch("custom_title", form);
  const planCustomDescription = Form.useWatch("custom_description", form);
  const planCustomMediaUrl = Form.useWatch("custom_media_url", form);

  const { result: channelsResult } = useList<{ id: number; name: string }>({ resource: "channels" });
  const { result: promotionsResult } = useList<{ id: number; title: string }>({ resource: "promotions" });
  const { result: newsResult } = useList<{ id: number; title: string }>({ resource: "news" });
  const { result: deliveriesResult } = useList<{ id: number; title: string }>({ resource: "deliveries" });
  const { result: eventsResult } = useList<{ id: number; title: string }>({ resource: "events" });

  const channels = channelsResult?.data ?? [];
  const promotions = promotionsResult?.data ?? [];
  const news = newsResult?.data ?? [];
  const deliveries = deliveriesResult?.data ?? [];
  const events = eventsResult?.data ?? [];

  const getContentOptions = (contentType: string) =>
    contentType === "promotion"
      ? promotions.map((p) => ({ label: p.title, value: p.id }))
      : contentType === "news"
        ? news.map((n) => ({ label: n.title, value: n.id }))
        : contentType === "delivery"
          ? deliveries.map((d) => ({ label: d.title, value: d.id }))
          : contentType === "event"
            ? events.map((e) => ({ label: e.title, value: e.id }))
            : [];

  const contentOptionsPlan = getContentOptions(planContentType);
  const channelOptions = channels.map((c) => ({ label: c.name, value: c.id }));

  return (
    <>
      <Form.Item label="Название плана" name="title" rules={[{ required: true }]}>
        <Input placeholder="Например: Анонс акции на выходные" />
      </Form.Item>
      <Form.Item
        label="Одно сообщение (если ничего не выбрано ниже)"
        name="content_type"
        rules={[{ required: true }]}
        help="Используется только если в блоке «Что отправить» ничего не выбрано — тогда отправится одна запись этого типа."
      >
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
      {planContentType === "custom" ? (
        <CustomContentBlock
          namePath={[]}
          form={form}
          previewTitle={planCustomTitle}
          previewDescription={planCustomDescription}
          previewMediaUrl={planCustomMediaUrl}
        />
      ) : planContentType && getContentOptions(planContentType).length > 0 ? (
        <Form.Item label="Какую запись отправить" name="content_id" extra="Только если в рассылке ниже ничего не выбрано.">
          <Select allowClear options={contentOptionsPlan} placeholder="Выберите из каталога" />
        </Form.Item>
      ) : planContentType && planContentType !== "custom" ? (
        <Form.Item extra="В этом разделе нет записей. Выберите пункты в блоке «Что отправить» ниже.">
          <Select disabled placeholder="Нет записей" options={[]} />
        </Form.Item>
      ) : null}

      <Form.Item
        label="Что отправить (выберите из каталога)"
        extra="Выберите готовые акции, новости, поставки или мероприятия — они отправятся по порядку. Можно добавить несколько. Либо один пункт «Свой контент» с произвольным текстом."
      >
        <Form.List name="items">
          {(fields, { add, remove }) => (
            <>
              {fields.map(({ key, name }) => (
                <Card key={key} size="small" style={{ marginBottom: 12 }}>
                  <Space direction="vertical" style={{ width: "100%" }}>
                    <OneMessageFields
                      namePath={["items", name]}
                      contentType={items[name]?.content_type}
                      contentOptions={getContentOptions(items[name]?.content_type)}
                      onContentTypeChange={() => {
                        const list = form?.getFieldValue("items") ?? [];
                        if (list[name]) {
                          list[name] = { ...list[name], content_id: null, custom_title: null, custom_description: null, custom_media_url: null };
                          form?.setFieldValue("items", [...list]);
                        }
                      }}
                      previewTitle={items[name]?.custom_title}
                      previewDescription={items[name]?.custom_description}
                      previewMediaUrl={items[name]?.custom_media_url}
                    />
                    <Button type="link" danger size="small" onClick={() => remove(name)}>
                      Убрать из рассылки
                    </Button>
                  </Space>
                </Card>
              ))}
              <Button
                type="dashed"
                onClick={() => add({ content_type: "promotion", content_id: null, custom_title: null, custom_description: null, custom_media_url: null })}
              >
                + Выбрать из каталога (акция / новость / поставка / мероприятие)
              </Button>
              <Button
                type="dashed"
                style={{ marginLeft: 8 }}
                onClick={() => add({ content_type: "custom", content_id: null, custom_title: null, custom_description: null, custom_media_url: null })}
              >
                + Свой текст
              </Button>
            </>
          )}
        </Form.List>
      </Form.Item>

      <Form.Item
        label="Дата и время отправки"
        name="scheduled_at"
        getValueProps={(v: string | null) => ({ value: v ? dayjs(v) : null })}
        normalize={(v: Dayjs | null) => (v ? v.toISOString() : null)}
        extra="Для автоматической отправки по времени выберите статус «Запланировано» и сохраните план — воркер отправит в указанное время."
      >
        <DatePicker showTime format="DD.MM.YYYY HH:mm" style={{ width: "100%" }} />
      </Form.Item>
      {isEdit && (
        <Form.Item label="Статус" name="status">
          <Select options={statusOptions} />
        </Form.Item>
      )}
      <Form.Item
        label="Каналы рассылки"
        name="channel_ids"
        rules={[{ required: true, type: "array", min: 1, message: "Выберите хотя бы один канал" }]}
        extra="В какие каналы отправить: бот (подписчики) и/или Telegram-каналы."
      >
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
    <Create title="Новая запись в контент плане" saveButtonProps={{ ...saveButtonProps, children: "Сохранить" }}>
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
    <Edit title="Редактирование контент плана" saveButtonProps={{ ...saveButtonProps, children: "Сохранить" }}>
      <Form {...formProps} layout="vertical">
        <ContentPlanForm isEdit />
      </Form>
    </Edit>
  );
}

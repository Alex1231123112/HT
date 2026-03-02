import { useRef, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Create, DeleteButton, Edit, EditButton, List, useForm, useTable } from "@refinedev/antd";
import { Button, Form, Input, message, Modal, Select, Space, Switch, Table } from "antd";
import type { UploadProps } from "antd";
import { InboxOutlined } from "@ant-design/icons";
import Dragger from "antd/es/upload/Dragger";
import { uploadContentFile } from "../providers";
import {
  getStoredTemplates,
  MESSAGE_TEMPLATES,
  PublicationPreview,
  RichTextEditor,
  setStoredTemplates,
} from "../components/PublicationEditor";
import type { TemplateItem } from "../components/PublicationEditor";

const MAX_SIZE_MB = 5;

function MediaUploadField() {
  const form = Form.useFormInstance();
  const uploadProps: UploadProps = {
    name: "file",
    multiple: false,
    maxCount: 1,
    showUploadList: false,
    beforeUpload: async (file) => {
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
      <p className="ant-upload-hint">Любой файл, не более {MAX_SIZE_MB} МБ. После загрузки ссылка подставится в поле ниже.</p>
    </Dragger>
  );
}

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

function ContentFormFields() {
  const form = Form.useFormInstance();
  const title = Form.useWatch("title", form);
  const description = Form.useWatch("description", form);
  const [userTemplates, setUserTemplates] = useState<TemplateItem[]>(getStoredTemplates);
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [newTemplateName, setNewTemplateName] = useState("");

  const allTemplates = useMemo(() => [...MESSAGE_TEMPLATES, ...userTemplates], [userTemplates]);

  const applyTemplate = (id: string) => {
    const t = allTemplates.find((x) => x.id === id);
    if (t && (t.title || t.description)) {
      form?.setFieldValue("title", t.title);
      form?.setFieldValue("description", t.description);
    }
  };

  const saveAsTemplate = () => {
    const t = title ?? "";
    const d = description ?? "";
    if (!newTemplateName.trim()) return;
    const newT: TemplateItem = {
      id: "user-" + Date.now(),
      label: newTemplateName.trim(),
      title: t,
      description: d,
    };
    const next = [...userTemplates, newT];
    setUserTemplates(next);
    setStoredTemplates(next);
    setSaveModalOpen(false);
    setNewTemplateName("");
  };

  return (
    <>
      <Form.Item
        label="Шаблон"
        help="Подставить готовый шаблон в заголовок и описание. Свои шаблоны сохраняются в браузере."
      >
        <Space.Compact style={{ width: "100%" }}>
          <Select
            placeholder="Выберите шаблон или свой сохранённый"
            style={{ flex: 1 }}
            allowClear
            options={allTemplates.map((t) => ({
              label: t.id.startsWith("user-") ? "📌 " + t.label : t.label,
              value: t.id,
            }))}
            onChange={applyTemplate}
          />
          <Button onClick={() => setSaveModalOpen(true)}>Сохранить как шаблон</Button>
        </Space.Compact>
      </Form.Item>
      <Form.Item label="Заголовок" name="title" rules={[{ required: true }]}>
        <Input placeholder="Заголовок" />
      </Form.Item>
      <Form.Item
        label="Описание"
        name="description"
        help="Выделите текст и выберите форматирование в панели сверху (жирный, курсив, подчёркивание, зачёркивание, цитата, моноширинный, ссылка). Предпросмотр — после сохранения."
      >
        <RichTextEditor />
      </Form.Item>
      <Form.Item label="Медиа (фото/видео для бота)" help="Загрузите файл или вставьте ссылку ниже.">
        <MediaUploadField />
      </Form.Item>
      <Form.Item label="Ссылка на медиа" name="image_url">
        <Input placeholder="Подставится после загрузки или вставьте URL вручную" />
      </Form.Item>
      <Form.Item noStyle shouldUpdate={(_, values) => values.image_url}>
        {({ getFieldValue }) => {
          const url = getFieldValue("image_url");
          if (!url || typeof url !== "string" || !url.trim()) return null;
          const isVideo = /\.(mp4|webm|mov)(\?|$)/i.test(url);
          return (
            <div style={{ marginTop: 8 }}>
              {isVideo ? (
                <span>Видео: <a href={url} target="_blank" rel="noopener noreferrer">{url}</a></span>
              ) : (
                <img src={url} alt="Превью" style={{ maxWidth: 200, maxHeight: 150, objectFit: "contain", border: "1px solid #d9d9d9", borderRadius: 4 }} />
              )}
            </div>
          );
        }}
      </Form.Item>
      <Form.Item
        label="Аудитория"
        name="user_type"
        initialValue="all"
        help="«Все» — контент виден всем. HoReCa/Розница — только выбранному сегменту в боте."
      >
        <Select options={audienceOptions} />
      </Form.Item>
      <Form.Item
        label="Активен"
        name="is_active"
        valuePropName="checked"
        initialValue={true}
        help="В боте показывается только активный контент. Включите, чтобы запись отображалась пользователям."
      >
        <Switch />
      </Form.Item>
      <Modal
        title="Сохранить как шаблон"
        open={saveModalOpen}
        onOk={saveAsTemplate}
        onCancel={() => { setSaveModalOpen(false); setNewTemplateName(""); }}
        okText="Сохранить"
      >
        <div style={{ marginBottom: 8 }}>Название шаблона:</div>
        <Input
          placeholder="Например: Акция на выходные"
          value={newTemplateName}
          onChange={(e) => setNewTemplateName(e.target.value)}
          onPressEnter={saveAsTemplate}
        />
      </Modal>
    </>
  );
}

export function ContentList({ resource }: { resource: "promotions" | "news" | "deliveries" }) {
  const { tableProps } = useTable<ContentRecord>({ resource });

  return (
    <List title="Контент" description="В боте показывается только контент с «Активен» = Да и с подходящей аудиторией (Все / тип пользователя).">
      <Table {...tableProps} rowKey="id" pagination={{ pageSize: 10, showSizeChanger: true }}>
        <Table.Column dataIndex="id" title="№" />
        <Table.Column dataIndex="title" title="Заголовок" />
        <Table.Column dataIndex="user_type" title="Аудитория" />
        <Table.Column<ContentRecord>
          dataIndex="is_active"
          title="Активен (виден в боте)"
          render={(value) => (value ? "Да" : "Нет")}
        />
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
  const navigate = useNavigate();
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [previewRecord, setPreviewRecord] = useState<ContentRecord | null>(null);
  const submittedValuesRef = useRef<Partial<ContentRecord> | null>(null);

  const { formProps, saveButtonProps } = useForm<ContentRecord>({
    resource,
    action: "create",
    defaultValues: { is_active: true, user_type: "all" },
    redirect: false,
    onMutationSuccess: (data) => {
      const record = (data as ContentRecord & { data?: ContentRecord })?.data ?? (data as ContentRecord);
      const fromForm = submittedValuesRef.current;
      setPreviewRecord({
        ...record,
        title: record?.title ?? fromForm?.title ?? "",
        description: record?.description ?? fromForm?.description ?? "",
        image_url: record?.image_url ?? fromForm?.image_url,
      } as ContentRecord);
      setPreviewModalOpen(true);
    },
  });

  const formPropsWithCapture = useMemo(
    () => ({
      ...formProps,
      onFinish: (values: Partial<ContentRecord>) => {
        submittedValuesRef.current = values;
        return formProps.onFinish?.(values);
      },
    }),
    [formProps]
  );

  const closePreviewAndGoToList = () => {
    setPreviewModalOpen(false);
    setPreviewRecord(null);
    navigate(`/${resource}`);
  };

  return (
    <Create title="Создание контента" saveButtonProps={{ ...saveButtonProps, children: "Сохранить" }}>
      <Form {...formPropsWithCapture} layout="vertical">
        <ContentFormFields />
      </Form>
      <Modal
        title="Предпросмотр после сохранения"
        open={previewModalOpen}
        onCancel={closePreviewAndGoToList}
        footer={
          <Button type="primary" onClick={closePreviewAndGoToList}>
            К списку
          </Button>
        }
        width={420}
      >
        {previewRecord && (
          <PublicationPreview
            title={previewRecord.title}
            description={previewRecord.description}
            mediaUrl={previewRecord.image_url}
          />
        )}
      </Modal>
    </Create>
  );
}

export function ContentEdit({ resource }: { resource: "promotions" | "news" | "deliveries" }) {
  const navigate = useNavigate();
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [previewRecord, setPreviewRecord] = useState<ContentRecord | null>(null);
  const submittedValuesRef = useRef<Partial<ContentRecord> | null>(null);

  const { formProps, saveButtonProps } = useForm<ContentRecord>({
    resource,
    action: "edit",
    redirect: false,
    onMutationSuccess: (data) => {
      const record = (data as ContentRecord & { data?: ContentRecord })?.data ?? (data as ContentRecord);
      const fromForm = submittedValuesRef.current;
      setPreviewRecord({
        ...record,
        id: (record as ContentRecord)?.id ?? (fromForm as ContentRecord)?.id,
        title: record?.title ?? fromForm?.title ?? "",
        description: record?.description ?? fromForm?.description ?? "",
        image_url: record?.image_url ?? fromForm?.image_url,
      } as ContentRecord);
      setPreviewModalOpen(true);
    },
  });

  const formPropsWithCapture = useMemo(
    () => ({
      ...formProps,
      onFinish: (values: Partial<ContentRecord>) => {
        submittedValuesRef.current = values;
        return formProps.onFinish?.(values);
      },
    }),
    [formProps]
  );

  const closePreview = () => {
    setPreviewModalOpen(false);
    setPreviewRecord(null);
  };

  const goToList = () => {
    setPreviewModalOpen(false);
    setPreviewRecord(null);
    navigate(`/${resource}`);
  };

  return (
    <Edit title="Редактирование контента" saveButtonProps={{ ...saveButtonProps, children: "Сохранить" }}>
      <Form {...formPropsWithCapture} layout="vertical">
        <ContentFormFields />
      </Form>
      <Modal
        title="Предпросмотр после сохранения"
        open={previewModalOpen}
        onCancel={closePreview}
        footer={
          <Space>
            <Button onClick={closePreview}>Остаться в форме</Button>
            <Button type="primary" onClick={goToList}>
              К списку
            </Button>
          </Space>
        }
        width={420}
      >
        {previewRecord && (
          <PublicationPreview
            title={previewRecord.title}
            description={previewRecord.description}
            mediaUrl={previewRecord.image_url}
          />
        )}
      </Modal>
    </Edit>
  );
}


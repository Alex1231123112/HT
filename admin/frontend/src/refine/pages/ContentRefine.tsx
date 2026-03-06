import { useEffect, useRef, useState, useMemo } from "react";
import { Create, DeleteButton, Edit, EditButton, List, useForm, useTable } from "@refinedev/antd";
import { Button, Divider, Form, Input, message, Modal, Select, Space, Switch, Table } from "antd";
import type { FormInstance } from "antd";
import type { UploadProps } from "antd";
import { InboxOutlined } from "@ant-design/icons";
import Dragger from "antd/es/upload/Dragger";
import { uploadContentFile } from "../providers";
import {
  getStoredTemplates,
  MESSAGE_TEMPLATES,
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
      <Divider orientation="left" plain style={{ marginTop: 0, marginBottom: 16, fontWeight: 600, color: "#262626" }}>
        Текст и шаблон
      </Divider>
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
        <Input placeholder="Заголовок" size="large" />
      </Form.Item>
      <Form.Item
        label="Описание"
        name="description"
        help="Выделите текст и выберите форматирование в панели сверху (как в Telegram)."
      >
        <RichTextEditor />
      </Form.Item>
      <Divider orientation="left" plain style={{ marginTop: 24, marginBottom: 16, fontWeight: 600, color: "#262626" }}>
        Медиа
      </Divider>
      <Form.Item label="Фото или видео для бота" help="Загрузите файл или вставьте ссылку ниже.">
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
      <Divider orientation="left" plain style={{ marginTop: 24, marginBottom: 16, fontWeight: 600, color: "#262626" }}>
        Публикация
      </Divider>
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

const PREVIEW_DEBOUNCE_MS = 400;
const PREVIEW_MESSAGE_TYPE = "UPDATE_PREVIEW";
const PREVIEW_WIDTH_MIN = 300;
const PREVIEW_WIDTH_MAX = 500;
const PREVIEW_WIDTH_DEFAULT = 360;

const FORM_COLUMN_STYLE: React.CSSProperties = {
  flex: 1,
  minWidth: 520,
  maxWidth: 800,
  padding: "28px 32px 32px",
  background: "#fff",
  borderRadius: 12,
  border: "1px solid #e8e8e8",
  boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
};

const PAGE_CONTENT_STYLE: React.CSSProperties = {
  maxWidth: 1320,
  margin: "0 auto",
  padding: "20px 28px 40px",
  width: "100%",
};

function sendPreviewToIframe(
  iframeRef: React.RefObject<HTMLIFrameElement | null>,
  payload: { title?: string; description?: string; image_url?: string | null }
) {
  try {
    iframeRef.current?.contentWindow?.postMessage(
      { type: PREVIEW_MESSAGE_TYPE, payload },
      window.location.origin
    );
  } catch {
    // ignore
  }
}

function PreviewColumn({
  form,
  previewWidth,
  iframeRef,
  onIframeLoad,
}: {
  form: FormInstance;
  previewWidth: number;
  iframeRef: React.RefObject<HTMLIFrameElement | null>;
  onIframeLoad: () => void;
}) {
  const title = Form.useWatch("title", form) ?? "";
  const description = Form.useWatch("description", form) ?? "";
  const image_url = Form.useWatch("image_url", form) ?? null;

  useEffect(() => {
    const t = setTimeout(() => {
      sendPreviewToIframe(iframeRef, {
        title: String(title ?? ""),
        description: String(description ?? ""),
        image_url: image_url != null && image_url !== "" ? String(image_url) : null,
      });
    }, PREVIEW_DEBOUNCE_MS);
    return () => clearTimeout(t);
  }, [title, description, image_url]);

  return (
    <div
      className="content-preview-column"
      style={{
        width: previewWidth,
        minWidth: PREVIEW_WIDTH_MIN,
        flexShrink: 0,
        display: "flex",
        flexDirection: "column",
        position: "sticky",
        top: 24,
        alignSelf: "flex-start",
      }}
    >
      <div style={{ marginBottom: 10, fontSize: 13, color: "#595959", fontWeight: 500 }}>
        Превью в Telegram
      </div>
      <iframe
        ref={iframeRef}
        src="/telegram-preview"
        title="Превью в стиле Telegram"
        onLoad={onIframeLoad}
        style={{
          width: "100%",
          height: 420,
          minHeight: 420,
          border: "1px solid #e8e8e8",
          borderRadius: 12,
          display: "block",
          flex: 1,
        }}
      />
    </div>
  );
}

function FormAndPreviewLayout({
  form,
  formProps,
  children,
}: {
  form: FormInstance;
  formProps: object;
  children: React.ReactNode;
}) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [previewWidth, setPreviewWidth] = useState(PREVIEW_WIDTH_DEFAULT);
  const [resizing, setResizing] = useState(false);
  const resizeStartRef = useRef({ x: 0, w: 0 });

  useEffect(() => {
    if (!resizing) return;
    const onMove = (e: MouseEvent) => {
      const delta = e.clientX - resizeStartRef.current.x;
      const w = Math.min(
        PREVIEW_WIDTH_MAX,
        Math.max(PREVIEW_WIDTH_MIN, resizeStartRef.current.w + delta)
      );
      setPreviewWidth(w);
    };
    const onUp = () => setResizing(false);
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [resizing]);

  const onResizerMouseDown = (e: React.MouseEvent) => {
    resizeStartRef.current = { x: e.clientX, w: previewWidth };
    setResizing(true);
  };

  const onIframeLoad = () => {
    sendPreviewToIframe(iframeRef, {
      title: String(form.getFieldValue("title") ?? ""),
      description: String(form.getFieldValue("description") ?? ""),
      image_url: form.getFieldValue("image_url") ?? null,
    });
  };

  return (
    <div className="content-form-preview-layout" style={{ ...LAYOUT_WRAPPER_STYLE, minHeight: 460 }}>
      <div className="content-form-column" style={FORM_COLUMN_STYLE}>
        <Form {...formProps} layout="vertical">
          {children}
        </Form>
      </div>
      <div
        className="content-form-preview-resizer"
        role="separator"
        onMouseDown={onResizerMouseDown}
        style={{
          width: 10,
          flexShrink: 0,
          cursor: "col-resize",
          background: resizing ? "#1890ff" : "#e8e8e8",
          borderRadius: 4,
          alignSelf: "stretch",
          userSelect: "none",
        }}
        aria-label="Изменить ширину превью"
        title="Потяните для изменения ширины превью"
      />
      <PreviewColumn
        form={form}
        previewWidth={previewWidth}
        iframeRef={iframeRef}
        onIframeLoad={onIframeLoad}
      />
    </div>
  );
}

const LAYOUT_WRAPPER_STYLE: React.CSSProperties = {
  display: "flex",
  width: "100%",
  alignItems: "flex-start",
  gap: 24,
};

export function ContentCreate({ resource }: { resource: "promotions" | "news" | "deliveries" }) {
  const { formProps, saveButtonProps, form } = useForm<ContentRecord>({
    resource,
    action: "create",
    defaultFormValues: { is_active: true, user_type: "all" },
    redirect: "list",
  });

  return (
    <Create title="Создание контента" saveButtonProps={{ ...saveButtonProps, children: "Сохранить" }}>
      <div style={PAGE_CONTENT_STYLE}>
        <FormAndPreviewLayout form={form} formProps={formProps}>
          <ContentFormFields />
        </FormAndPreviewLayout>
      </div>
    </Create>
  );
}

export function ContentEdit({ resource }: { resource: "promotions" | "news" | "deliveries" }) {
  const { formProps, saveButtonProps, form } = useForm<ContentRecord>({
    resource,
    action: "edit",
    redirect: false,
  });

  return (
    <Edit title="Редактирование контента" saveButtonProps={{ ...saveButtonProps, children: "Сохранить" }}>
      <div style={PAGE_CONTENT_STYLE}>
        <FormAndPreviewLayout form={form} formProps={formProps}>
          <ContentFormFields />
        </FormAndPreviewLayout>
      </div>
    </Edit>
  );
}


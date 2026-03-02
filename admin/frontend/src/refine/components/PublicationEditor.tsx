import React, { useState, useMemo, useEffect } from "react";
import { Button, Input, Modal, Select, Space } from "antd";
import type { FormInstance } from "antd";
// @ts-expect-error no types for react-quill in tsconfig
import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";

const STORAGE_KEY = "content_plan_templates";

export type TemplateItem = { id: string; label: string; title: string; description: string };

/** Встроенные шаблоны */
export const MESSAGE_TEMPLATES: TemplateItem[] = [
  { id: "", label: "Без шаблона", title: "", description: "" },
  {
    id: "promo",
    label: "Акция",
    title: "Акция",
    description:
      "Специальное предложение для вас.<br><br>Условия и сроки уточняйте у менеджера.<br><br>Подробнее: <a href=\"https://example.com\">перейти</a>",
  },
  {
    id: "news",
    label: "Новость",
    title: "Новость",
    description: "Важная информация.<br><br>Подробности в описании ниже.",
  },
  {
    id: "event",
    label: "Мероприятие",
    title: "Приглашаем на мероприятие",
    description:
      "Дата и время: укажите здесь.<br>Место: укажите здесь.<br><br><a href=\"https://example.com\">Регистрация</a>",
  },
];

export function getStoredTemplates(): TemplateItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw);
    return Array.isArray(arr) ? arr : [];
  } catch {
    return [];
  }
}

export function setStoredTemplates(list: TemplateItem[]) {
  const toStore = list.filter((t) => t.id.startsWith("user-"));
  localStorage.setItem(STORAGE_KEY, JSON.stringify(toStore));
}

const ALLOWED_TAGS = new Set(["B", "I", "U", "S", "CODE", "PRE", "A", "BR", "P", "STRONG", "EM", "BLOCKQUOTE"]);

/** Разрешаем только теги, которые поддерживает Telegram. Итеративный обход — без переполнения стека на глубоком HTML. */
function sanitizeHtml(html: string): string {
  if (!html || !html.trim()) return "";
  try {
    const div = document.createElement("div");
    div.innerHTML = html;
    const stack: Node[] = [div];
    while (stack.length > 0) {
      const node = stack.pop()!;
      if (node.nodeType !== Node.ELEMENT_NODE) continue;
      const el = node as Element;
      const tag = el.tagName.toUpperCase();
      if (tag === "STRONG") {
        el.outerHTML = "<b>" + el.innerHTML + "</b>";
        continue;
      }
      if (tag === "EM") {
        el.outerHTML = "<i>" + el.innerHTML + "</i>";
        continue;
      }
      if (!ALLOWED_TAGS.has(tag)) {
        const parent = el.parentNode;
        const children: Node[] = [];
        while (el.firstChild) children.push(el.firstChild);
        for (const c of children) parent?.insertBefore(c, el);
        parent?.removeChild(el);
        for (let i = children.length - 1; i >= 0; i--) stack.push(children[i]);
        continue;
      }
      for (let i = el.childNodes.length - 1; i >= 0; i--) stack.push(el.childNodes[i]);
    }
    return div.innerHTML;
  } catch {
    return "";
  }
}

const PREVIEW_DEBOUNCE_MS = 400;

/** Превью публикации в стиле Telegram. Описание обновляется с задержкой, чтобы не блокировать ввод. */
export function PublicationPreview({
  title,
  description,
  mediaUrl,
}: {
  title?: string | null;
  description?: string | null;
  mediaUrl?: string | null;
}) {
  const [debouncedDescription, setDebouncedDescription] = useState(description ?? "");
  useEffect(() => {
    const t = setTimeout(() => setDebouncedDescription(description ?? ""), PREVIEW_DEBOUNCE_MS);
    return () => clearTimeout(t);
  }, [description]);
  const safeDesc = useMemo(() => sanitizeHtml(debouncedDescription), [debouncedDescription]);
  return (
    <div
      style={{
        border: "1px solid #d9d9d9",
        borderRadius: 8,
        padding: 12,
        background: "#fafafa",
        fontSize: 14,
        maxWidth: 360,
      }}
    >
      <div style={{ marginBottom: 8, fontWeight: 600 }}>{title || "(без заголовка)"}</div>
      {mediaUrl && (
        <div style={{ marginBottom: 8, color: "#888", fontSize: 12 }}>
          [Медиа: {mediaUrl.length > 40 ? mediaUrl.slice(0, 40) + "…" : mediaUrl}]
        </div>
      )}
      {safeDesc ? (
        <div
          style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}
          dangerouslySetInnerHTML={{ __html: safeDesc }}
        />
      ) : (
        <span style={{ color: "#999" }}>(нет описания)</span>
      )}
    </div>
  );
}

/** Модули Quill: форматирование как в Telegram — выдели текст и выбери в панели сверху */
const QUILL_MODULES = {
  toolbar: [
    ["bold", "italic", "underline", "strike"],
    ["blockquote", "code"],
    ["link"],
    ["clean"],
  ],
  clipboard: { matchVisual: false },
};

const QUILL_STYLE = {
  minHeight: 140,
  marginBottom: 0,
};

/** Пустое содержимое Quill (чтобы не было цикла onChange при инициализации) */
const QUILL_EMPTY = "<p><br></p>";

/** Визуальный редактор текста (как в Telegram / Word): форматирование видно сразу */
export function RichTextEditor({
  value = "",
  onChange,
  placeholder,
}: {
  value?: string;
  onChange?: (v: string) => void;
  placeholder?: string;
}) {
  const v = value ?? "";
  const displayValue = v === "" ? QUILL_EMPTY : v;
  return (
    <div
      className="rich-editor-wrap"
      style={{
        border: "1px solid #d9d9d9",
        borderRadius: 6,
        overflow: "auto",
        minHeight: 200,
        resize: "vertical",
      }}
    >
      <ReactQuill
        theme="snow"
        value={displayValue}
        onChange={(val) => {
          const next = val === QUILL_EMPTY ? "" : val;
          if (next !== v) onChange?.(next);
        }}
        modules={QUILL_MODULES}
        placeholder={placeholder ?? "Выделите текст и выберите форматирование в панели сверху: жирный, курсив, подчёркивание, зачёркивание, цитата, моноширинный, ссылка. Или используйте Ctrl+B, Ctrl+I, Ctrl+U и т.д."}
        style={QUILL_STYLE}
      />
    </div>
  );
}

/** Единый блок «Свой контент»: шаблоны (в т.ч. свои), редактор как в Word/Telegram, превью */
export function CustomContentBlock({
  namePath,
  form,
  previewTitle,
  previewDescription,
  previewMediaUrl,
}: {
  namePath: (string | number)[];
  form: FormInstance;
  previewTitle?: string | null;
  previewDescription?: string | null;
  previewMediaUrl?: string | null;
}) {
  const [userTemplates, setUserTemplates] = useState<TemplateItem[]>(getStoredTemplates);
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [newTemplateName, setNewTemplateName] = useState("");

  const allTemplates = useMemo(
    () => [...MESSAGE_TEMPLATES, ...userTemplates],
    [userTemplates]
  );

  const setField = (field: string, value: string | null) => {
    form.setFieldValue(namePath.length ? [...namePath, field] : field, value);
  };

  const applyTemplate = (id: string) => {
    const t = allTemplates.find((x) => x.id === id);
    if (t && (t.title || t.description)) {
      setField("custom_title", t.title);
      setField("custom_description", t.description);
    }
  };

  const saveAsTemplate = () => {
    const title = previewTitle ?? "";
    const description = previewDescription ?? "";
    if (!newTemplateName.trim()) return;
    const newT: TemplateItem = {
      id: "user-" + Date.now(),
      label: newTemplateName.trim(),
      title,
      description,
    };
    const next = [...userTemplates, newT];
    setUserTemplates(next);
    setStoredTemplates(next);
    setSaveModalOpen(false);
    setNewTemplateName("");
  };

  return (
    <>
      <Space direction="vertical" style={{ width: "100%" }} size="middle">
        <div>
          <div style={{ marginBottom: 4, fontWeight: 500 }}>Шаблон</div>
          <Space.Compact style={{ width: "100%" }}>
            <Select
              placeholder="Выберите шаблон или свой сохранённый"
              style={{ flex: 1 }}
              allowClear
              options={allTemplates.map((t) => ({ label: t.id.startsWith("user-") ? "📌 " + t.label : t.label, value: t.id }))}
              onChange={applyTemplate}
            />
            <Button onClick={() => setSaveModalOpen(true)}>Сохранить как шаблон</Button>
          </Space.Compact>
          <div style={{ fontSize: 12, color: "#888", marginTop: 4 }}>
            Шаблон подставит заголовок и описание. Свои шаблоны сохраняются в браузере.
          </div>
        </div>

        <Form.Item
          name={namePath.length ? [...namePath, "custom_title"] : ("custom_title" as const)}
          label="Заголовок"
          style={{ marginBottom: 16 }}
        >
          <Input placeholder="Заголовок сообщения" />
        </Form.Item>

        <Form.Item
          name={namePath.length ? [...namePath, "custom_description"] : ("custom_description" as const)}
          label="Описание"
          style={{ marginBottom: 16 }}
        >
          <RichTextEditor placeholder="Выделите текст и выберите форматирование в панели сверху (как в Telegram)." />
        </Form.Item>

        <Form.Item
          name={namePath.length ? [...namePath, "custom_media_url"] : ("custom_media_url" as const)}
          label="Ссылка на картинку или видео"
        >
          <Input placeholder="https://..." />
        </Form.Item>

        <div>
          <div style={{ marginBottom: 4, fontWeight: 500 }}>Предпросмотр</div>
          <div style={{ fontSize: 12, color: "#888", marginBottom: 6 }}>Как будет выглядеть в Telegram</div>
          <PublicationPreview
            title={previewTitle}
            description={previewDescription}
            mediaUrl={previewMediaUrl}
          />
        </div>
      </Space>

      <Modal
        title="Сохранить как шаблон"
        open={saveModalOpen}
        onOk={saveAsTemplate}
        onCancel={() => { setSaveModalOpen(false); setNewTemplateName(""); }}
        okText="Сохранить"
      >
        <div style={{ marginBottom: 8 }}>Название шаблона (например: «Акция на выходные»):</div>
        <Input
          placeholder="Название шаблона"
          value={newTemplateName}
          onChange={(e) => setNewTemplateName(e.target.value)}
          onPressEnter={saveAsTemplate}
        />
      </Modal>
    </>
  );
}

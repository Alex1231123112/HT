import { Create, DeleteButton, Edit, EditButton, List, SaveButton, useForm, useTable } from "@refinedev/antd";
import { Form, Input, message, Select, Switch, Table } from "antd";
import type { UploadProps } from "antd";
import { InboxOutlined } from "@ant-design/icons";
import Dragger from "antd/es/upload/Dragger";
import { uploadContentFile } from "../providers";

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
  const { formProps, saveButtonProps } = useForm<ContentRecord>({
    resource,
    action: "create",
    defaultValues: { is_active: true, user_type: "all" },
  });

  return (
    <Create title="Создание контента" saveButtonProps={saveButtonProps}>
      <Form {...formProps} layout="vertical">
        <Form.Item label="Заголовок" name="title" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="Описание" name="description">
          <Input.TextArea />
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
      </Form>
      <SaveButton {...saveButtonProps}>Сохранить</SaveButton>
    </Create>
  );
}

export function ContentEdit({ resource }: { resource: "promotions" | "news" | "deliveries" }) {
  const { formProps, saveButtonProps } = useForm<ContentRecord>({ resource, action: "edit" });

  return (
    <Edit title="Редактирование контента" saveButtonProps={saveButtonProps}>
      <Form {...formProps} layout="vertical">
        <Form.Item label="Заголовок" name="title" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="Описание" name="description">
          <Input.TextArea />
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
          help="«Все» — виден всем в боте. HoReCa/Розница — только этому сегменту."
        >
          <Select options={audienceOptions} />
        </Form.Item>
        <Form.Item
          label="Активен"
          name="is_active"
          valuePropName="checked"
          help="В боте показывается только активный контент."
        >
          <Switch />
        </Form.Item>
      </Form>
      <SaveButton {...saveButtonProps}>Сохранить</SaveButton>
    </Edit>
  );
}


import { useAdmin } from "../context/AdminContext";
import { ContentKind } from "../types";

const TITLES: Record<ContentKind, string> = { promotions: "Акции", news: "Новинки", deliveries: "Приходы" };

export function ContentPage({ kind }: { kind: ContentKind }) {
  const { contentForms, setContentForms, contentByKind, saveContent, deleteContent, duplicatePromotion, uploadContentMedia } = useAdmin();
  const form = contentForms[kind];
  const items = contentByKind[kind];

  const setField = (field: string, value: string | boolean | null) => {
    setContentForms((prev) => ({ ...prev, [kind]: { ...prev[kind], [field]: value } }));
  };

  return (
    <section className="card">
      <h2>{TITLES[kind]}</h2>
      <div className="grid-form">
        <input value={form.title} placeholder="Заголовок" onChange={(e) => setField("title", e.target.value)} />
        <input value={form.image_url ?? ""} placeholder="Media URL" onChange={(e) => setField("image_url", e.target.value)} />
        <textarea value={form.description} placeholder="Описание" onChange={(e) => setField("description", e.target.value)} />
        <select value={form.user_type} onChange={(e) => setField("user_type", e.target.value)}>
          <option value="all">all</option>
          <option value="horeca">horeca</option>
          <option value="retail">retail</option>
        </select>
        <input
          type="datetime-local"
          value={form.published_at ? form.published_at.slice(0, 16) : ""}
          onChange={(e) => setField("published_at", e.target.value ? new Date(e.target.value).toISOString() : null)}
        />
        <label className="row left">
          <input type="checkbox" checked={form.is_active} onChange={(e) => setField("is_active", e.target.checked)} />
          Опубликовано
        </label>
        <input type="file" onChange={(e) => uploadContentMedia(kind, e.target.files?.[0] ?? null)} />
      </div>
      <div className="row left">
        <button onClick={() => saveContent(kind)}>{form.id ? "Сохранить" : "Создать"}</button>
      </div>

      {items.map((item) => (
        <div key={item.id} className="row">
          <span>
            #{item.id} {item.title} ({item.user_type}) {item.is_active ? "🟢 Активна" : "🟡 Черновик"}
          </span>
          <div className="row">
            <button onClick={() => setContentForms((prev) => ({ ...prev, [kind]: { ...item } }))}>Редактировать</button>
            {kind === "promotions" && <button onClick={() => duplicatePromotion(item.id)}>Дублировать</button>}
            <button onClick={() => deleteContent(kind, item.id)}>Удалить</button>
          </div>
        </div>
      ))}
    </section>
  );
}

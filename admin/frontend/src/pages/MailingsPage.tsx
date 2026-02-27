import { useMemo, useState } from "react";
import { useCreate, useCustomMutation, useList, useNotification, useUpdate } from "@refinedev/core";

type WizardStep = 1 | 2 | 3 | 4;

type UserItem = { id: number; user_type: "horeca" | "retail" | "all"; establishment: string };
type Mailing = {
  id: number;
  text: string;
  target_type: "all" | "horeca" | "retail" | "custom";
  scheduled_at: string | null;
  status: "draft" | "scheduled" | "sent" | "cancelled";
};

const targetLabels: Record<Mailing["target_type"], string> = {
  all: "все",
  horeca: "HoReCa",
  retail: "розница",
  custom: "выбранные заведения",
};

const statusLabels: Record<Mailing["status"], string> = {
  draft: "черновик",
  scheduled: "запланирована",
  sent: "отправлена",
  cancelled: "отменена",
};

export function MailingsPage() {
  const { result: usersResp } = useList<UserItem>({ resource: "users" });
  const users = usersResp?.data ?? [];
  const establishments = useMemo(() => Array.from(new Set(users.map((u) => u.establishment))), [users]);
  const { result: mailingsResp, query: mailingsQuery } = useList<Mailing>({ resource: "mailings" });
  const mailings = mailingsResp?.data ?? [];
  const { open } = useNotification();
  const [mailingPreview, setMailingPreview] = useState("");
  const [mailingStats, setMailingStats] = useState<Record<number, { sent: number; opened: number; clicked: number; open_rate: number; ctr: number }>>({});
  const [step, setStep] = useState<WizardStep>(1);
  const [mailForm, setMailForm] = useState({
    text: "",
    target_type: "all" as "all" | "horeca" | "retail" | "custom",
    media_type: "none" as "none" | "photo" | "video",
    media_url: "",
    scheduled_at: "",
    establishment: "",
    speed: "medium" as "high" | "medium" | "low",
  });
  const { mutateAsync: createMailing } = useCreate();
  const { mutateAsync: updateMailing } = useUpdate();
  const { mutateAsync: customMutation } = useCustomMutation();

  const recipients = useMemo(() => {
    if (mailForm.target_type === "all") return users.length;
    if (mailForm.target_type === "horeca") return users.filter((item) => item.user_type === "horeca").length;
    if (mailForm.target_type === "retail") return users.filter((item) => item.user_type === "retail").length;
    return users.filter((item) => item.establishment === mailForm.establishment).length;
  }, [mailForm.target_type, mailForm.establishment, users]);

  const submitCreate = async () => {
    let customTargets: number[] | null = null;
    if (mailForm.target_type === "custom") {
      customTargets = users.filter((item) => item.establishment === mailForm.establishment).map((item) => item.id);
    }
    await createMailing({
      resource: "mailings",
      values: {
        text: mailForm.text,
        target_type: mailForm.target_type,
        media_type: mailForm.media_type,
        media_url: mailForm.media_url || null,
        custom_targets: customTargets,
        scheduled_at: mailForm.scheduled_at || null,
        speed: mailForm.speed,
      },
    });
    setMailForm((prev) => ({ ...prev, text: "", media_url: "", scheduled_at: "" }));
    await mailingsQuery.refetch();
    open?.({ type: "success", message: "Рассылка сохранена" });
  };

  const callAction = async (id: number, action: string) => {
    if (action === "delete") {
      await updateMailing({ resource: "mailings", id, values: { status: "cancelled" } });
      await mailingsQuery.refetch();
      return;
    }
    if (action === "stats") {
      const token = localStorage.getItem("token") ?? "";
      const response = await fetch(`${import.meta.env.VITE_API_URL ?? "http://localhost:8000/api"}/mailings/${id}/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = (await response.json()) as { data: { sent: number; opened: number; clicked: number; open_rate: number; ctr: number } };
      const data = payload.data ?? { sent: 0, opened: 0, clicked: 0, open_rate: 0, ctr: 0 };
      setMailingStats((prev) => ({ ...prev, [id]: data }));
      return;
    }
    const response = await customMutation({
      url: `/mailings/${id}/${action}`,
      method: "post",
      values: {},
    });
    if (action === "preview") {
      setMailingPreview(`Текст: ${String((response.data as Record<string, unknown>)?.text ?? "")}`);
    }
    await mailingsQuery.refetch();
  };

  return (
    <section className="card">
      <h2>Мастер рассылок (шаг {step}/4)</h2>
      {step === 1 && (
        <div className="grid-form">
          <label>
            Аудитория
            <select
              value={mailForm.target_type}
              onChange={(e) => setMailForm((prev) => ({ ...prev, target_type: e.target.value as "all" | "horeca" | "retail" | "custom" }))}
            >
              <option value="all">Все пользователи</option>
              <option value="horeca">Только HoReCa</option>
              <option value="retail">Только Retail</option>
              <option value="custom">Конкретные заведения</option>
            </select>
          </label>
          {mailForm.target_type === "custom" && (
            <label>
              Заведение
              <select value={mailForm.establishment} onChange={(e) => setMailForm((prev) => ({ ...prev, establishment: e.target.value }))}>
                <option value="">Выберите заведение</option>
                {establishments.map((establishment) => (
                  <option key={establishment} value={establishment}>
                    {establishment}
                  </option>
                ))}
              </select>
            </label>
          )}
          <p>Получателей: {recipients}</p>
        </div>
      )}

      {step === 2 && (
        <div className="grid-form">
          <textarea value={mailForm.text} onChange={(e) => setMailForm((prev) => ({ ...prev, text: e.target.value }))} placeholder="Текст рассылки" />
          <select value={mailForm.media_type} onChange={(e) => setMailForm((prev) => ({ ...prev, media_type: e.target.value as "none" | "photo" | "video" }))}>
            <option value="none">Без медиа</option>
            <option value="photo">Фото</option>
            <option value="video">Видео</option>
          </select>
          <input
            value={mailForm.media_url}
            onChange={(e) => setMailForm((prev) => ({ ...prev, media_url: e.target.value }))}
            placeholder="Ссылка на медиа"
          />
        </div>
      )}

      {step === 3 && (
        <div className="grid-form">
          <p>Тестовая отправка и предпросмотр</p>
          <div className="row left">
            <button
              onClick={async () => {
                await submitCreate();
              }}
            >
              Сохранить черновик
            </button>
          </div>
          <p className="muted">После создания черновика используйте кнопки Тест/Предпросмотр в списке ниже.</p>
        </div>
      )}

      {step === 4 && (
        <div className="grid-form">
          <label>
            Отправка
            <input
              type="datetime-local"
              value={mailForm.scheduled_at}
              onChange={(e) =>
                setMailForm((prev) => ({ ...prev, scheduled_at: e.target.value ? new Date(e.target.value).toISOString() : "" }))
              }
            />
          </label>
          <label>
            Скорость
            <select value={mailForm.speed} onChange={(e) => setMailForm((prev) => ({ ...prev, speed: e.target.value as "high" | "medium" | "low" }))}>
              <option value="high">Максимальная</option>
              <option value="medium">Средняя</option>
              <option value="low">Низкая</option>
            </select>
          </label>
          <div className="row left">
            <button onClick={submitCreate}>Подтвердить и сохранить</button>
          </div>
        </div>
      )}

      <div className="row">
        <button disabled={step === 1} onClick={() => setStep((prev) => (prev === 1 ? 1 : ((prev - 1) as WizardStep)))}>
          Назад
        </button>
        <button disabled={step === 4} onClick={() => setStep((prev) => (prev === 4 ? 4 : ((prev + 1) as WizardStep)))}>
          Далее
        </button>
      </div>

      {mailingPreview && <pre className="preview">{mailingPreview}</pre>}

      <h3>Список рассылок</h3>
      {mailings.map((mailing) => (
        <div key={mailing.id} className="card nested">
          <div className="row">
            <span>
              #{mailing.id} [{statusLabels[mailing.status]}] аудитория={targetLabels[mailing.target_type]}
            </span>
            <span>{mailing.scheduled_at ? new Date(mailing.scheduled_at).toLocaleString() : "сразу"}</span>
          </div>
          <p>{mailing.text}</p>
          <div className="row left">
            <button onClick={() => callAction(mailing.id, "preview")}>Предпросмотр</button>
            <button onClick={() => callAction(mailing.id, "test-send")}>Тест</button>
            <button onClick={() => callAction(mailing.id, "send")}>Отправить</button>
            <button onClick={() => callAction(mailing.id, "cancel")}>Отменить</button>
            <button onClick={() => callAction(mailing.id, "retry")}>Повторить</button>
            <button onClick={() => callAction(mailing.id, "stats")}>Статистика</button>
            <button onClick={() => callAction(mailing.id, "delete")}>Удалить</button>
          </div>
          {mailingStats[mailing.id] && (
            <p className="muted">
              доставлено={mailingStats[mailing.id].sent}, открыто={mailingStats[mailing.id].opened}, кликов=
              {mailingStats[mailing.id].clicked}, открываемость={mailingStats[mailing.id].open_rate}%, CTR=
              {mailingStats[mailing.id].ctr}%
            </p>
          )}
        </div>
      ))}
    </section>
  );
}

import { useState } from "react";

import { apiPost, apiPut } from "../api";
import { useAdmin } from "../context/AdminContext";

export function SettingsPage() {
  const { systemSettings, setSystemSettings, saveSettings, createBackup, backups, downloadBackup, role } = useAdmin();
  const [tab, setTab] = useState<"general" | "security" | "backups">("general");
  const [schedule, setSchedule] = useState("0 2 * * *");
  const [retentionDays, setRetentionDays] = useState("30");
  const [restoreFile, setRestoreFile] = useState("");

  return (
    <section className="card">
      <div className="row left">
        <button onClick={() => setTab("general")}>Общие</button>
        <button onClick={() => setTab("security")}>Безопасность</button>
        <button onClick={() => setTab("backups")}>Бэкапы</button>
      </div>

      {tab === "general" && (
        <>
          {Object.entries(systemSettings).map(([key, value]) => (
            <div className="row" key={key}>
              <span>{key}</span>
              <input value={value} onChange={(e) => setSystemSettings((prev) => ({ ...prev, [key]: e.target.value }))} />
            </div>
          ))}
          <button onClick={saveSettings}>Сохранить изменения</button>
        </>
      )}

      {tab === "security" && (
        <div className="grid-form">
          <p>Текущая роль: {role}</p>
          <p className="muted">Параметры rate-limit/CORS/CSRF задаются через system settings и env.</p>
        </div>
      )}

      {tab === "backups" && (
        <>
          <div className="row left">
            <button onClick={createBackup}>Создать бэкап сейчас</button>
          </div>
          <div className="grid-form">
            <input value={schedule} onChange={(e) => setSchedule(e.target.value)} placeholder="cron schedule" />
            <input value={retentionDays} onChange={(e) => setRetentionDays(e.target.value)} placeholder="retention days" />
            <button onClick={() => apiPut("/settings/backup-policy", { schedule, retention_days: Number(retentionDays) })}>
              Сохранить политику
            </button>
          </div>
          <div className="grid-form">
            <input value={restoreFile} onChange={(e) => setRestoreFile(e.target.value)} placeholder="filename for restore" />
            <button onClick={() => apiPost(`/settings/restore/${restoreFile}?dry_run=true`, {}, true)}>Проверить restore</button>
            <button onClick={() => apiPost(`/settings/restore/${restoreFile}?dry_run=false`, {}, true)}>Применить restore</button>
          </div>
          {backups.map((item) => (
            <div className="row" key={item}>
              <span>{item}</span>
              <button onClick={() => downloadBackup(item)}>Скачать</button>
            </div>
          ))}
        </>
      )}
    </section>
  );
}

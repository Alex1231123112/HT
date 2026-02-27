import { useState } from "react";

import { useAdmin } from "../context/AdminContext";

export function AdminsPage() {
  const { admins, createAdmin, updateAdmin, deleteAdmin } = useAdmin();
  const [form, setForm] = useState({ username: "", password: "", role: "manager" as "superadmin" | "admin" | "manager" });

  return (
    <section className="card">
      <h2>Администраторы</h2>
      <div className="grid-form">
        <input value={form.username} placeholder="username" onChange={(e) => setForm((prev) => ({ ...prev, username: e.target.value }))} />
        <input value={form.password} type="password" placeholder="password" onChange={(e) => setForm((prev) => ({ ...prev, password: e.target.value }))} />
        <select value={form.role} onChange={(e) => setForm((prev) => ({ ...prev, role: e.target.value as "superadmin" | "admin" | "manager" }))}>
          <option value="superadmin">superadmin</option>
          <option value="admin">admin</option>
          <option value="manager">manager</option>
        </select>
      </div>
      <button onClick={() => createAdmin(form)}>Добавить администратора</button>
      {admins.map((item) => (
        <div className="row" key={item.id}>
          <span>
            #{item.id} {item.username} ({item.role}) {item.is_active ? "🟢" : "🔴"}
          </span>
          <div className="row">
            <button onClick={() => updateAdmin(item.id, { is_active: !item.is_active })}>
              {item.is_active ? "Деактивировать" : "Активировать"}
            </button>
            <button onClick={() => deleteAdmin(item.id)}>Удалить</button>
          </div>
        </div>
      ))}
    </section>
  );
}

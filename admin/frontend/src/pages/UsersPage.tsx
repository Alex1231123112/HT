import { useMemo, useState } from "react";

import { useAdmin } from "../context/AdminContext";
import { User } from "../types";

export function UsersPage() {
  const {
    search,
    setSearch,
    userTypeFilter,
    setUserTypeFilter,
    filteredUsers,
    creatingUser,
    setCreatingUser,
    createUser,
    editingUser,
    setEditingUser,
    saveUser,
    deleteUser,
    exportUsers,
  } = useAdmin();
  const [dateFilter, setDateFilter] = useState<"all" | "today" | "week" | "month">("all");
  const [activityFilter, setActivityFilter] = useState<"all" | "active" | "inactive">("all");
  const [page, setPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const pageSize = 25;

  const displayUsers = useMemo(() => {
    const now = new Date();
    const users = filteredUsers.filter((item) => {
      if (dateFilter === "all" || !item.registered_at) return true;
      const created = new Date(item.registered_at);
      const diff = now.getTime() - created.getTime();
      if (dateFilter === "today") return diff <= 24 * 60 * 60 * 1000;
      if (dateFilter === "week") return diff <= 7 * 24 * 60 * 60 * 1000;
      return diff <= 30 * 24 * 60 * 60 * 1000;
    });
    return users.filter((item) => {
      if (activityFilter === "all") return true;
      return activityFilter === "active" ? item.is_active !== false : item.is_active === false;
    });
  }, [filteredUsers, dateFilter, activityFilter]);

  const totalPages = Math.max(1, Math.ceil(displayUsers.length / pageSize));
  const pageUsers = displayUsers.slice((page - 1) * pageSize, page * pageSize);

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]));
  };

  const bulkDeactivate = async () => {
    for (const id of selectedIds) {
      const user = displayUsers.find((item) => item.id === id);
      if (!user) continue;
      setEditingUser({ ...user, is_active: false });
      await saveUser();
    }
    setSelectedIds([]);
  };

  return (
    <section className="card">
      <h2>Пользователи</h2>
      <div className="row controls">
        <input placeholder="Поиск username/заведения" value={search} onChange={(e) => setSearch(e.target.value)} />
        <select value={userTypeFilter} onChange={(e) => setUserTypeFilter(e.target.value as "all" | "horeca" | "retail")}>
          <option value="all">Все типы</option>
          <option value="horeca">HoReCa</option>
          <option value="retail">Retail</option>
        </select>
        <select value={dateFilter} onChange={(e) => setDateFilter(e.target.value as "all" | "today" | "week" | "month")}>
          <option value="all">Дата: всё время</option>
          <option value="today">Сегодня</option>
          <option value="week">Неделя</option>
          <option value="month">Месяц</option>
        </select>
        <select value={activityFilter} onChange={(e) => setActivityFilter(e.target.value as "all" | "active" | "inactive")}>
          <option value="all">Активность: любая</option>
          <option value="active">Активен</option>
          <option value="inactive">Неактивен</option>
        </select>
        <button onClick={exportUsers}>Экспорт CSV</button>
      </div>
      {selectedIds.length > 0 && (
        <div className="row left">
          <button onClick={bulkDeactivate}>Массово деактивировать ({selectedIds.length})</button>
        </div>
      )}
      <h3>Добавить пользователя</h3>
      <div className="grid-form">
        <input placeholder="Telegram ID" value={creatingUser.id} onChange={(e) => setCreatingUser((p) => ({ ...p, id: e.target.value }))} />
        <input placeholder="username" value={creatingUser.username} onChange={(e) => setCreatingUser((p) => ({ ...p, username: e.target.value }))} />
        <input placeholder="first_name" value={creatingUser.first_name} onChange={(e) => setCreatingUser((p) => ({ ...p, first_name: e.target.value }))} />
        <input placeholder="last_name" value={creatingUser.last_name} onChange={(e) => setCreatingUser((p) => ({ ...p, last_name: e.target.value }))} />
        <select value={creatingUser.user_type} onChange={(e) => setCreatingUser((p) => ({ ...p, user_type: e.target.value as "horeca" | "retail" }))}>
          <option value="horeca">HoReCa</option>
          <option value="retail">Retail</option>
        </select>
        <input placeholder="Заведение" value={creatingUser.establishment} onChange={(e) => setCreatingUser((p) => ({ ...p, establishment: e.target.value }))} />
      </div>
      <button onClick={createUser}>Создать</button>

      {editingUser && <EditUserCard editingUser={editingUser} setEditingUser={setEditingUser} saveUser={saveUser} />}

      {pageUsers.map((user) => (
        <div key={user.id} className="row">
          <div className="row left">
            <input type="checkbox" checked={selectedIds.includes(user.id)} onChange={() => toggleSelect(user.id)} />
            <span>
              #{user.id} | {user.username ?? "no_username"} | {user.user_type} | {user.establishment}
            </span>
          </div>
          <div className="row">
            <button onClick={() => setEditingUser(user)}>Редактировать</button>
            <button onClick={() => deleteUser(user.id)}>Удалить</button>
          </div>
        </div>
      ))}

      <div className="row">
        <button disabled={page <= 1} onClick={() => setPage((prev) => Math.max(1, prev - 1))}>
          ◀
        </button>
        <span>
          Страница {page} / {totalPages}
        </span>
        <button disabled={page >= totalPages} onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}>
          ▶
        </button>
      </div>
    </section>
  );
}

function EditUserCard({
  editingUser,
  setEditingUser,
  saveUser,
}: {
  editingUser: User;
  setEditingUser: (user: User | null) => void;
  saveUser: () => Promise<void>;
}) {
  return (
    <div className="card nested">
      <h3>Редактирование пользователя #{editingUser.id}</h3>
      <div className="grid-form">
        <input
          value={editingUser.username ?? ""}
          onChange={(e) => setEditingUser({ ...editingUser, username: e.target.value })}
          placeholder="username"
        />
        <input
          value={editingUser.first_name ?? ""}
          onChange={(e) => setEditingUser({ ...editingUser, first_name: e.target.value })}
          placeholder="first_name"
        />
        <input
          value={editingUser.last_name ?? ""}
          onChange={(e) => setEditingUser({ ...editingUser, last_name: e.target.value })}
          placeholder="last_name"
        />
        <input
          value={editingUser.establishment}
          onChange={(e) => setEditingUser({ ...editingUser, establishment: e.target.value })}
          placeholder="establishment"
        />
        <select
          value={editingUser.user_type}
          onChange={(e) => setEditingUser({ ...editingUser, user_type: e.target.value as "horeca" | "retail" | "all" })}
        >
          <option value="horeca">HoReCa</option>
          <option value="retail">Retail</option>
        </select>
        <label className="row left">
          <input type="checkbox" checked={editingUser.is_active !== false} onChange={(e) => setEditingUser({ ...editingUser, is_active: e.target.checked })} />
          Активен
        </label>
      </div>
      <div className="row">
        <button onClick={saveUser}>Сохранить</button>
        <button onClick={() => setEditingUser(null)}>Отмена</button>
      </div>
    </div>
  );
}

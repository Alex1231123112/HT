import { Authenticated, CanAccess, Refine } from "@refinedev/core";
import routerProvider, {
  CatchAllNavigate,
  DocumentTitleHandler,
  NavigateToResource,
  UnsavedChangesNotifier,
} from "@refinedev/react-router";
import { ErrorComponent, RefineThemes, ThemedLayout, useNotificationProvider } from "@refinedev/antd";
import { ConfigProvider, Spin } from "antd";
import React, { Suspense, useEffect } from "react";
import { Outlet, Route, Routes } from "react-router-dom";

import { accessControlProvider, authProvider, dataProvider } from "./refine/providers";
import "./styles.css";

const PageFallback = (
  <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: 240 }}>
    <Spin tip="Загрузка…" />
  </div>
);

const LoginPage = React.lazy(() => import("./pages/LoginPage").then((m) => ({ default: m.LoginPage })));
const DashboardPage = React.lazy(() => import("./pages/DashboardPage").then((m) => ({ default: m.DashboardPage })));
const MailingsPage = React.lazy(() => import("./pages/MailingsPage").then((m) => ({ default: m.MailingsPage })));
const AnalyticsPage = React.lazy(() => import("./pages/AnalyticsPage").then((m) => ({ default: m.AnalyticsPage })));
const AdminsList = React.lazy(() => import("./refine/pages/AdminsRefine").then((m) => ({ default: m.AdminsList })));
const AdminsCreate = React.lazy(() => import("./refine/pages/AdminsRefine").then((m) => ({ default: m.AdminsCreate })));
const AdminsEdit = React.lazy(() => import("./refine/pages/AdminsRefine").then((m) => ({ default: m.AdminsEdit })));
const ContentList = React.lazy(() => import("./refine/pages/ContentRefine").then((m) => ({ default: m.ContentList })));
const ContentCreate = React.lazy(() => import("./refine/pages/ContentRefine").then((m) => ({ default: m.ContentCreate })));
const ContentEdit = React.lazy(() => import("./refine/pages/ContentRefine").then((m) => ({ default: m.ContentEdit })));
const LogsList = React.lazy(() => import("./refine/pages/LogsRefine").then((m) => ({ default: m.LogsList })));
const SettingsEdit = React.lazy(() => import("./refine/pages/SettingsRefine").then((m) => ({ default: m.SettingsEdit })));
const UsersList = React.lazy(() => import("./refine/pages/UsersRefine").then((m) => ({ default: m.UsersList })));
const UsersCreate = React.lazy(() => import("./refine/pages/UsersRefine").then((m) => ({ default: m.UsersCreate })));
const UsersEdit = React.lazy(() => import("./refine/pages/UsersRefine").then((m) => ({ default: m.UsersEdit })));
const ManagersList = React.lazy(() => import("./refine/pages/ManagersRefine").then((m) => ({ default: m.ManagersList })));
const ManagersCreate = React.lazy(() => import("./refine/pages/ManagersRefine").then((m) => ({ default: m.ManagersCreate })));
const ManagersEdit = React.lazy(() => import("./refine/pages/ManagersRefine").then((m) => ({ default: m.ManagersEdit })));
const EstablishmentsList = React.lazy(() =>
  import("./refine/pages/EstablishmentsRefine").then((m) => ({ default: m.EstablishmentsList }))
);
const EstablishmentsCreate = React.lazy(() =>
  import("./refine/pages/EstablishmentsRefine").then((m) => ({ default: m.EstablishmentsCreate }))
);
const EstablishmentsEdit = React.lazy(() =>
  import("./refine/pages/EstablishmentsRefine").then((m) => ({ default: m.EstablishmentsEdit }))
);
const ChannelsList = React.lazy(() => import("./refine/pages/ChannelsRefine").then((m) => ({ default: m.ChannelsList })));
const ChannelsCreate = React.lazy(() => import("./refine/pages/ChannelsRefine").then((m) => ({ default: m.ChannelsCreate })));
const ChannelsEdit = React.lazy(() => import("./refine/pages/ChannelsRefine").then((m) => ({ default: m.ChannelsEdit })));
const ContentPlanList = React.lazy(() =>
  import("./refine/pages/ContentPlanRefine").then((m) => ({ default: m.ContentPlanList }))
);
const ContentPlanCreate = React.lazy(() =>
  import("./refine/pages/ContentPlanRefine").then((m) => ({ default: m.ContentPlanCreate }))
);
const ContentPlanEdit = React.lazy(() =>
  import("./refine/pages/ContentPlanRefine").then((m) => ({ default: m.ContentPlanEdit }))
);
const EventsList = React.lazy(() => import("./refine/pages/EventsRefine").then((m) => ({ default: m.EventsList })));
const EventsCreate = React.lazy(() => import("./refine/pages/EventsRefine").then((m) => ({ default: m.EventsCreate })));
const EventsEdit = React.lazy(() => import("./refine/pages/EventsRefine").then((m) => ({ default: m.EventsEdit })));

export default function App() {
  const notificationProvider = useNotificationProvider();
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.key.toLowerCase() === "s") {
        event.preventDefault();
        window.dispatchEvent(new CustomEvent("app:save"));
      }
      if (event.ctrlKey && event.key === "Enter") {
        event.preventDefault();
        window.dispatchEvent(new CustomEvent("app:submit"));
      }
      if (event.key === "/") {
        const target = document.activeElement as HTMLElement | null;
        const isTyping = target?.tagName === "INPUT" || target?.tagName === "TEXTAREA";
        if (!isTyping) {
          event.preventDefault();
          (document.querySelector("[data-global-search='true']") as HTMLInputElement | null)?.focus();
        }
      }
      if (event.key === "Escape") {
        (document.activeElement as HTMLElement | null)?.blur();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  return (
    <ConfigProvider theme={RefineThemes.Blue}>
      <Refine
          dataProvider={dataProvider}
          authProvider={authProvider}
          accessControlProvider={accessControlProvider}
          routerProvider={routerProvider}
        notificationProvider={notificationProvider}
          resources={[
            { name: "dashboard", list: "/dashboard", meta: { label: "Дашборд" } },
            { name: "users", list: "/users", create: "/users/create", edit: "/users/edit/:id", meta: { label: "Пользователи" } },
            { name: "managers", list: "/managers", create: "/managers/create", edit: "/managers/edit/:id", meta: { label: "Менеджеры" } },
            { name: "establishments", list: "/establishments", create: "/establishments/create", edit: "/establishments/edit/:id", meta: { label: "Заведения" } },
            {
              name: "promotions",
              list: "/promotions",
              create: "/promotions/create",
              edit: "/promotions/edit/:id",
              meta: { label: "Акции" },
            },
            { name: "news", list: "/news", create: "/news/create", edit: "/news/edit/:id", meta: { label: "Новости" } },
            {
              name: "deliveries",
              list: "/deliveries",
              create: "/deliveries/create",
              edit: "/deliveries/edit/:id",
              meta: { label: "Поставки" },
            },
            { name: "events", list: "/events", create: "/events/create", edit: "/events/edit/:id", meta: { label: "Мероприятия" } },
            { name: "mailings", list: "/mailings", meta: { label: "Рассылки" } },
            { name: "channels", list: "/channels", create: "/channels/create", edit: "/channels/edit/:id", meta: { label: "Каналы рассылки" } },
            { name: "content_plan", list: "/content-plan", create: "/content-plan/create", edit: "/content-plan/edit/:id", meta: { label: "Контент план" } },
            { name: "analytics", list: "/analytics", meta: { label: "Аналитика" } },
            { name: "logs", list: "/logs", meta: { label: "Логи" } },
            { name: "settings", list: "/settings", edit: "/settings/edit/default", meta: { label: "Настройки" } },
            { name: "admins", list: "/admins", create: "/admins/create", edit: "/admins/edit/:id", meta: { label: "Админы" } },
          ]}
          options={{ syncWithLocation: true, warnWhenUnsavedChanges: true }}
        >
          <Suspense fallback={PageFallback}>
          <Routes>
            <Route
              element={
                <Authenticated key="private" fallback={<CatchAllNavigate to="/login" />}>
                  <ThemedLayout>
                    <Outlet />
                  </ThemedLayout>
                </Authenticated>
              }
            >
              <Route index element={<NavigateToResource resource="dashboard" />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/managers">
                <Route
                  index
                  element={
                    <CanAccess resource="users" action="list" fallback={<ErrorComponent />}>
                      <ManagersList />
                    </CanAccess>
                  }
                />
                <Route
                  path="create"
                  element={
                    <CanAccess resource="users" action="create" fallback={<ErrorComponent />}>
                      <ManagersCreate />
                    </CanAccess>
                  }
                />
                <Route
                  path="edit/:id"
                  element={
                    <CanAccess resource="users" action="edit" fallback={<ErrorComponent />}>
                      <ManagersEdit />
                    </CanAccess>
                  }
                />
              </Route>
              <Route path="/establishments">
                <Route
                  index
                  element={
                    <CanAccess resource="establishments" action="list" fallback={<ErrorComponent />}>
                      <EstablishmentsList />
                    </CanAccess>
                  }
                />
                <Route
                  path="create"
                  element={
                    <CanAccess resource="establishments" action="create" fallback={<ErrorComponent />}>
                      <EstablishmentsCreate />
                    </CanAccess>
                  }
                />
                <Route
                  path="edit/:id"
                  element={
                    <CanAccess resource="establishments" action="edit" fallback={<ErrorComponent />}>
                      <EstablishmentsEdit />
                    </CanAccess>
                  }
                />
              </Route>
              <Route path="/users">
                <Route
                  index
                  element={
                    <CanAccess resource="users" action="list" fallback={<ErrorComponent />}>
                      <UsersList />
                    </CanAccess>
                  }
                />
                <Route
                  path="create"
                  element={
                    <CanAccess resource="users" action="create" fallback={<ErrorComponent />}>
                      <UsersCreate />
                    </CanAccess>
                  }
                />
                <Route
                  path="edit/:id"
                  element={
                    <CanAccess resource="users" action="edit" fallback={<ErrorComponent />}>
                      <UsersEdit />
                    </CanAccess>
                  }
                />
              </Route>
              <Route path="/promotions">
                <Route index element={<ContentList resource="promotions" />} />
                <Route path="create" element={<ContentCreate resource="promotions" />} />
                <Route path="edit/:id" element={<ContentEdit resource="promotions" />} />
              </Route>
              <Route path="/news">
                <Route index element={<ContentList resource="news" />} />
                <Route path="create" element={<ContentCreate resource="news" />} />
                <Route path="edit/:id" element={<ContentEdit resource="news" />} />
              </Route>
              <Route path="/deliveries">
                <Route index element={<ContentList resource="deliveries" />} />
                <Route path="create" element={<ContentCreate resource="deliveries" />} />
                <Route path="edit/:id" element={<ContentEdit resource="deliveries" />} />
              </Route>
              <Route path="/events">
                <Route index element={<EventsList />} />
                <Route path="create" element={<EventsCreate />} />
                <Route path="edit/:id" element={<EventsEdit />} />
              </Route>
              <Route path="/mailings" element={<MailingsPage />} />
              <Route path="/channels">
                <Route index element={<ChannelsList />} />
                <Route path="create" element={<ChannelsCreate />} />
                <Route path="edit/:id" element={<ChannelsEdit />} />
              </Route>
              <Route path="/content-plan">
                <Route index element={<ContentPlanList />} />
                <Route path="create" element={<ContentPlanCreate />} />
                <Route path="edit/:id" element={<ContentPlanEdit />} />
              </Route>
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route
                path="/logs"
                element={
                  <CanAccess resource="logs" action="list" fallback={<ErrorComponent />}>
                    <LogsList />
                  </CanAccess>
                }
              />
              <Route
                path="/settings/edit/default"
                element={
                  <CanAccess resource="settings" action="edit" fallback={<ErrorComponent />}>
                    <SettingsEdit />
                  </CanAccess>
                }
              />
              <Route
                path="/settings"
                element={
                  <CanAccess resource="settings" action="list" fallback={<ErrorComponent />}>
                    <SettingsEdit />
                  </CanAccess>
                }
              />
              <Route
                path="/admins"
                element={
                  <CanAccess resource="admins" action="list" fallback={<ErrorComponent />}>
                    <AdminsList />
                  </CanAccess>
                }
              />
              <Route
                path="/admins/create"
                element={
                  <CanAccess resource="admins" action="create" fallback={<ErrorComponent />}>
                    <AdminsCreate />
                  </CanAccess>
                }
              />
              <Route
                path="/admins/edit/:id"
                element={
                  <CanAccess resource="admins" action="edit" fallback={<ErrorComponent />}>
                    <AdminsEdit />
                  </CanAccess>
                }
              />
            </Route>
            <Route
              path="/login"
              element={
                <Authenticated key="public" fallback={<LoginPage />}>
                  <NavigateToResource resource="dashboard" />
                </Authenticated>
              }
            />
            <Route path="*" element={<ErrorComponent />} />
          </Routes>
          <UnsavedChangesNotifier />
          <DocumentTitleHandler />
          </Suspense>
      </Refine>
    </ConfigProvider>
  );
}

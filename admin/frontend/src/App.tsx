import { Authenticated, CanAccess, Refine } from "@refinedev/core";
import routerProvider, {
  CatchAllNavigate,
  DocumentTitleHandler,
  NavigateToResource,
  UnsavedChangesNotifier,
} from "@refinedev/react-router";
import { ErrorComponent, RefineThemes, ThemedLayout, useNotificationProvider } from "@refinedev/antd";
import { ConfigProvider } from "antd";
import { Outlet, Route, Routes } from "react-router-dom";

import { AnalyticsPage } from "./pages/AnalyticsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { MailingsPage } from "./pages/MailingsPage";
import { accessControlProvider, authProvider, dataProvider } from "./refine/providers";
import { AdminsCreate, AdminsEdit, AdminsList } from "./refine/pages/AdminsRefine";
import { ContentCreate, ContentEdit, ContentList } from "./refine/pages/ContentRefine";
import { LogsList } from "./refine/pages/LogsRefine";
import { SettingsEdit } from "./refine/pages/SettingsRefine";
import { UsersCreate, UsersEdit, UsersList } from "./refine/pages/UsersRefine";
import "./styles.css";

export default function App() {
  const notificationProvider = useNotificationProvider();

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
            { name: "mailings", list: "/mailings", meta: { label: "Рассылки" } },
            { name: "analytics", list: "/analytics", meta: { label: "Аналитика" } },
            { name: "logs", list: "/logs", meta: { label: "Логи" } },
            { name: "settings", list: "/settings", edit: "/settings/edit/default", meta: { label: "Настройки" } },
            { name: "admins", list: "/admins", create: "/admins/create", edit: "/admins/edit/:id", meta: { label: "Админы" } },
          ]}
          options={{ syncWithLocation: true, warnWhenUnsavedChanges: true }}
        >
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
              <Route path="/mailings" element={<MailingsPage />} />
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
      </Refine>
    </ConfigProvider>
  );
}

import React, { Suspense } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Spin } from "antd";
import App from "./App";
import "antd/dist/reset.css";

class AppErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { error: Error | null }
> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("App crash:", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div
          style={{
            padding: 24,
            fontFamily: "sans-serif",
            maxWidth: 600,
            margin: "40px auto",
            background: "#fff3cd",
            border: "1px solid #ffc107",
            borderRadius: 8,
          }}
        >
          <h2>Ошибка загрузки</h2>
          <pre style={{ overflow: "auto", fontSize: 12 }}>
            {this.state.error.message}
          </pre>
          <button
            onClick={() => window.location.reload()}
            style={{ marginTop: 12, padding: "8px 16px" }}
          >
            Обновить страницу
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

const rootEl = document.getElementById("root");
if (!rootEl) {
  document.body.innerHTML = "<p style='margin:2rem;font-family:sans-serif;'>Ошибка: элемент #root не найден.</p>";
} else {
  try {
    const AppLoader = (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
        <Spin size="large" tip="Загрузка админки…" />
      </div>
    );
    ReactDOM.createRoot(rootEl).render(
      <React.StrictMode>
        <AppErrorBoundary>
          <BrowserRouter>
            <Suspense fallback={AppLoader}>
              <App />
            </Suspense>
          </BrowserRouter>
        </AppErrorBoundary>
      </React.StrictMode>,
    );
  } catch (e) {
    rootEl.innerHTML = `<p style="margin:2rem;font-family:sans-serif;color:#c00;">Ошибка запуска: ${e instanceof Error ? e.message : String(e)}</p>`;
    console.error(e);
  }
}

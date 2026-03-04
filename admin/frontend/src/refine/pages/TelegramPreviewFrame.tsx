import React, { useEffect, useState, useMemo } from "react";

const MESSAGE_TYPE = "UPDATE_PREVIEW";

type Payload = {
  title?: string | null;
  description?: string | null;
  image_url?: string | null;
};

function sanitizeForPreview(html: string): string {
  if (!html || !html.trim()) return "";
  let s = html
    .replace(/<script\b[\s\S]*?<\/script>/gi, "")
    .replace(/<style\b[\s\S]*?<\/style>/gi, "")
    .replace(/\s+on\w+="[^"]*"/gi, "")
    .replace(/\s+rel="[^"]*"/gi, "")
    .replace(/\s+target="[^"]*"/gi, "")
    .trim();
  // Меньше пробелов: абзацы превращаем в переносы
  s = s.replace(/<\/p>\s*<p[^>]*>/gi, "<br>").replace(/<p[^>]*>/gi, "").replace(/<\/p>/gi, "<br>");
  return s.replace(/<br>\s*<br>/gi, "<br>").trim();
}

const allowedOrigin = typeof window !== "undefined" ? window.location.origin : "";

export function TelegramPreviewFrame() {
  const [payload, setPayload] = useState<Payload>({ title: null, description: null, image_url: null });

  useEffect(() => {
    const handler = (event: MessageEvent) => {
      if (event.origin !== allowedOrigin) return;
      const d = event.data;
      if (!d || d.type !== MESSAGE_TYPE || !d.payload) return;
      setPayload({
        title: d.payload.title ?? null,
        description: d.payload.description ?? null,
        image_url: d.payload.image_url ?? null,
      });
    };
    window.addEventListener("message", handler);
    return () => window.removeEventListener("message", handler);
  }, []);

  const safeDesc = useMemo(
    () => (payload.description ? sanitizeForPreview(String(payload.description)) : ""),
    [payload.description]
  );
  const title = (payload.title ?? "").trim() || "(без заголовка)";
  const mediaUrl = (payload.image_url ?? "").trim() || null;
  const isVideo = mediaUrl ? /\.(mp4|webm|mov)(\?|$)/i.test(mediaUrl) : false;

  return (
    <>
      <style>{`
        .telegram-preview-body a {
          color: #6ab2f2;
          text-decoration: none;
          background: none !important;
          padding: 0;
          border: none;
          border-radius: 0;
          box-shadow: none;
          outline: none;
        }
        .telegram-preview-body a:hover { text-decoration: underline; }
        .telegram-preview-body p, .telegram-preview-body div { margin: 0 0 0.2em 0; line-height: 1.35; }
        .telegram-preview-body p:last-child, .telegram-preview-body div:last-child { margin-bottom: 0; }
      `}</style>
      <div
        style={{
          margin: 0,
          minHeight: "100vh",
          background: "#0e1621",
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
        padding: 16,
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        fontSize: 15,
      }}
    >
      <div
        style={{
          maxWidth: 360,
          width: "100%",
          background: "#17212b",
          borderRadius: 12,
          padding: "12px 14px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
        }}
      >
        <div
          style={{
            background: "#2b5278",
            color: "#fff",
            borderRadius: 10,
            padding: "10px 12px",
            marginBottom: 8,
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: 6 }}>{title}</div>
          {mediaUrl && (
            <div style={{ marginBottom: 8, fontSize: 12, opacity: 0.9 }}>
              {isVideo ? (
                <span>[Видео]</span>
              ) : (
                <img
                  src={mediaUrl}
                  alt=""
                  style={{
                    maxWidth: "100%",
                    maxHeight: 200,
                    objectFit: "contain",
                    borderRadius: 6,
                    display: "block",
                  }}
                />
              )}
            </div>
          )}
          {safeDesc ? (
            <div
              style={{
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                lineHeight: 1.4,
              }}
              className="telegram-preview-body"
              dangerouslySetInnerHTML={{ __html: safeDesc }}
            />
          ) : (
            <span style={{ opacity: 0.7 }}>(нет описания)</span>
          )}
        </div>
      </div>
    </div>
    </>
  );
}

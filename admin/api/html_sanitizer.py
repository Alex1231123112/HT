"""
Санитизация HTML по белому списку в стиле Telegram.
Разрешены только теги: b, strong, i, em, u, s, del, strike, code, pre, a, br, p, blockquote.
У ссылок — только атрибут href и схемы http, https, mailto. Остальное удаляется (в т.ч. <script>).
"""
import bleach

# Теги, как в Telegram
ALLOWED_TAGS = [
    "b", "strong", "i", "em", "u",
    "s", "del", "strike",
    "code", "pre", "a", "br", "p", "blockquote",
]

ALLOWED_ATTRIBUTES = {"a": ["href"]}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def sanitize_html_for_telegram(html: str | None) -> str:
    """Очищает HTML: только разрешённые теги и безопасные ссылки. Остальное удаляется."""
    if not html or not html.strip():
        return ""
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    ).strip()

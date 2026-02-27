from config.settings import Settings


def test_prod_cors_filters_non_https():
    settings = Settings(APP_ENV="prod", ALLOWED_ORIGINS="http://localhost:5173,https://admin.example.com")
    assert settings.cors_origins == ["https://admin.example.com"]


def test_dev_cors_keeps_all_origins():
    settings = Settings(APP_ENV="dev", ALLOWED_ORIGINS="http://localhost:5173,https://admin.example.com")
    assert settings.cors_origins == ["http://localhost:5173", "https://admin.example.com"]

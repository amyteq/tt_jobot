from pydantic import Field, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class LLMProviderSettings(BaseSettings):
    base_url: str = Field("https://your-llm-endpoint/v1", env="LLM_BASE_URL")
    api_key: str = Field(..., env="LLM_API_KEY")
    model: str = "gpt-4o-mini"
    timeout_s: int = 60

class EmbeddingsProviderSettings(BaseSettings):
    model: str = "text-embedding-3-large"
    dim: int = 3072

class PostgresSettings(BaseSettings):
    dsn: str = Field("postgresql+psycopg://user:pass@db:5432/jobot", env="POSTGRES_DSN")
    use_pgvector: bool = True

class S3Settings(BaseSettings):
    endpoint: str = Field("http://minio:9000", env="S3_ENDPOINT")
    bucket: str = "jobot"
    access_key: str = Field(..., env="S3_KEY")
    secret_key: str = Field(..., env="S3_SECRET")

class SlackNotifierSettings(BaseSettings):
    bot_token: str = Field(..., env="SLACK_BOT_TOKEN")
    channel: str = "#job-alerts"

class EmailNotifierSettings(BaseSettings):
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    username: EmailStr = Field(..., env="SMTP_USER")
    password: str = Field(..., env="SMTP_PASS")

class SeekSiteSettings(BaseSettings):
    enabled: bool = True
    email: EmailStr = Field("you@example.com", env="SEEK_EMAIL")
    password: str = Field(..., env="SEEK_PASS")
    region: str = "AU"

class LinkedInSiteSettings(BaseSettings):
    enabled: bool = True
    cookies_path: str = "./secrets/linkedin_cookies.json"
    easy_apply_only: bool = True

class ToptalSiteSettings(BaseSettings):
    enabled: bool = False

class RulesSettings(BaseSettings):
    location_allow: List[str] = ["Melbourne", "Sydney", "Remote-AU"]
    industry_allow: List[str] = ["Software", "Data", "AI/ML"]
    seniority: List[str] = ["Mid", "Senior", "Staff"]
    skills_must: List[str] = ["Python", "FastAPI", "Postgres"]
    skills_nice: List[str] = ["TypeScript", "AWS", "Kubernetes"]
    min_score: float = 0.70

class ApplySettings(BaseSettings):
    human_in_loop: bool = True
    attach_cover_letter: bool = True
    rate_limit_per_site_per_hour: int = 20
    captcha_provider: str = "manual"

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        yaml_file="config/config.yaml",
        yaml_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore" # Ignore extra fields in config.yaml
    )
    env: str = "dev"
    base_url: str = "https://your-api.example.com"
    timezone: str = "Australia/Melbourne"

    providers: dict[str, BaseSettings] = {
        "llm": LLMProviderSettings(),
        "embeddings": EmbeddingsProviderSettings(),
    }
    storages: dict[str, BaseSettings] = {
        "postgres": PostgresSettings(),
        "s3": S3Settings(),
    }
    notifiers: dict[str, BaseSettings] = {
        "slack": SlackNotifierSettings(),
        "email": EmailNotifierSettings(),
    }
    sites: dict[str, BaseSettings] = {
        "seek": SeekSiteSettings(),
        "linkedin": LinkedInSiteSettings(),
        "toptal": ToptalSiteSettings(),
    }
    rules: RulesSettings = RulesSettings()
    apply: ApplySettings = ApplySettings()

settings = AppSettings()
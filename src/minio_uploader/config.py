import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

def _to_bool(v: str | None, default: bool = True) -> bool:
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")

@dataclass
class S3Config:
    endpoint: str
    access_key: str
    secret_key: str
    region: str = "us-east-1"
    verify_ssl: bool = True

    @classmethod
    def from_env(cls) -> "S3Config":
        return cls(
            endpoint=os.environ.get("S3_ENDPOINT", "http://127.0.0.1:9000"),
            access_key=os.environ.get("S3_ACCESS_KEY", ""),
            secret_key=os.environ.get("S3_SECRET_KEY", ""),
            region=os.environ.get("S3_REGION", "us-east-1"),
            verify_ssl=_to_bool(os.environ.get("S3_VERIFY_SSL"), default=True),
        )
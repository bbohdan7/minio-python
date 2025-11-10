import boto3
from botocore.config import Config
from .config import S3Config

def get_s3_client(cfg: S3Config | None = None):
    if cfg is None:
        cfg = S3Config.from_env()
    session = boto3.session.Session(
        aws_access_key_id=cfg.access_key,
        aws_secret_access_key=cfg.secret_key,
        region_name=cfg.region,
    )
    return session.client(
        "s3",
        endpoint_url=cfg.endpoint,
        verify=cfg.verify_ssl,
        config=Config(s3={"addressing_style": "path"}),
    )
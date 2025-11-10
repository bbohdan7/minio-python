from __future__ import annotations
import argparse, json, sys

import boto3
from .config import S3Config
from .client import get_s3_client
from pathlib import Path
import mimetypes

def cmd_config_show(cfg: S3Config):
    print(json.dumps({
        "endpoint": cfg.endpoint,
        "region": cfg.region,
        "verify_ssl": cfg.verify_ssl,
        "access_key_set": bool(cfg.access_key),
        "secret_key_set": bool(cfg.secret_key),
    }, indent=2))

def cmd_ensure_bucket(bucket: str, cfg: S3Config):
    s3 = get_s3_client(cfg)
    # idempotent: якщо нема — створимо, якщо є — просто підтвердимо
    try:
        s3.head_bucket(Bucket=bucket)
        print(f"[ok] bucket exists: {bucket}")
        return
    except Exception:
        # створимо й перевіримо ще раз
        s3.create_bucket(Bucket=bucket)
        print(f"[created] bucket: {bucket}")

def guess_content_type(path: Path) -> str:
    ctype, _ = mimetypes.guess_type(str(path))
    return ctype or "application/octet-stream"

def cmd_upload_file(bucket: str, local_path: str, key: str | None, cfg: S3Config):
    s3 = get_s3_client(cfg)
    p = Path(local_path).resolve()
    if not p.is_file():
        raise SystemExit(f"not a file: {p}")
    if key is None:
        key = p.name
    extra = {"ContentType": guess_content_type(p)}
    s3.upload_file(str(p), bucket, key, ExtraArgs=extra)
    print(f"[uploaded] s3://{bucket}/{key} ({extra['ContentType']})")

def cmd_ls(bucket: str, prefix: str, cfg: S3Config):
    s3 = get_s3_client(cfg)
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix or "")
    total = 0
    for page in pages:
        for obj in page.get("Contents", []) or []:
            total += 1
            print(f"{obj['Key']}\t{obj['Size']}")
    print(f"[ok] {total} objects")

def cmd_list_buckets(cfg: S3Config):
    """Виводить перелік усіх бакетів у MinIO/S3"""
    s3 = boto3.client(
        "s3",
        endpoint_url=cfg.endpoint,
        aws_access_key_id=cfg.access_key,
        aws_secret_access_key=cfg.secret_key,
        region_name=cfg.region,
        verify=cfg.verify_ssl,
    )
    resp = s3.list_buckets()
    for b in resp.get("Buckets", []):
        print(f"{b['Name']}\t{b['CreationDate']}")

def build_parser():
    p = argparse.ArgumentParser(prog="minio-uploader", description="Work with MinIO via S3 (boto3)")
    sub = p.add_subparsers(dest="cmd", required=True)
    
    p.subparsers = sub

    # спільні опції
    p_common = argparse.ArgumentParser(add_help=False)
    p_common.add_argument("--endpoint", default=None)
    p_common.add_argument("--access-key", default=None)
    p_common.add_argument("--secret-key", default=None)
    p_common.add_argument("--region", default=None)
    p_common.add_argument("--verify-ssl", default=None, choices=["true","false"])

    def cfg_from_args(a) -> S3Config:
        cfg = S3Config.from_env()
        if a.endpoint: cfg.endpoint = a.endpoint
        if a.access_key: cfg.access_key = a.access_key
        if a.secret_key: cfg.secret_key = a.secret_key
        if a.region: cfg.region = a.region
        if a.verify_ssl is not None: cfg.verify_ssl = (a.verify_ssl.lower() == "true")
        return cfg

    # config-show
    sp = sub.add_parser("config-show", parents=[p_common], help="Show resolved config")
    sp.set_defaults(func=lambda a: cmd_config_show(cfg_from_args(a)))

    # ensure-bucket
    sp = sub.add_parser("ensure-bucket", parents=[p_common], help="Create bucket if missing")
    sp.add_argument("bucket")
    sp.set_defaults(func=lambda a: cmd_ensure_bucket(a.bucket, cfg_from_args(a)))

    # upload-file
    sp = sub.add_parser("upload-file", parents=[p_common], help="Upload a single file")
    sp.add_argument("bucket")
    sp.add_argument("path", help="local file path")
    sp.add_argument("--key", help="S3 object key (default: filename)")
    sp.set_defaults(func=lambda a: cmd_upload_file(a.bucket, a.path, a.key, cfg_from_args(a)))

    # ls
    sp = sub.add_parser("ls", parents=[p_common], help="List objects")
    sp.add_argument("bucket")
    sp.add_argument("--prefix", default="")
    sp.set_defaults(func=lambda a: cmd_ls(a.bucket, a.prefix, cfg_from_args(a)))

    # list-buckets
    sp = sub.add_parser("buckets", parents=[p_common], help="List all buckets")
    sp.set_defaults(func=lambda a: cmd_list_buckets(cfg_from_args(a)))

    sp = sub.add_parser("help", help="Show help for a command or the whole CLI")
    sp.add_argument("topic", nargs="?", help="Optional subcommand name, e.g. 'upload-file'")

    def _help_cb(a, parser=p):
        choices = parser.subparsers.choices
        if a.topic and a.topic in choices:
            choices[a.topic].print_help()
        else:
            parser.print_help()

    sp.set_defaults(func=_help_cb)

    return p

def main(argv=None):
    argv = argv or sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)

if __name__ == "__main__":
    main()
## 🚀 Швидкий старт

### 1️⃣ Клонувати репозиторій
```bash
git clone <repo_url> minio_test
cd minio_test

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -U pip setuptools wheel
python -m pip install -e .

nano .env

S3_ENDPOINT=http://<API_ENDPOINT_MINIO>:9000
S3_ACCESS_KEY=miniouser
S3_SECRET_KEY=miniopass
S3_REGION=us-east-1
S3_VERIFY_SSL=false

minio-uploader ensure-bucket my-bucket

echo "Hello MinIO!" > hello.txt
minio-uploader upload-file my-bucket ./hello.txt --key uploads/hello.txt

minio-uploader ls my-bucket --prefix uploads/


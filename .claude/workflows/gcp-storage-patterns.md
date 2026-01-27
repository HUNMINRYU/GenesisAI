---
description: Google Cloud Storage Patterns & Best Practices
---

# GCP 스토리지 패턴 (GCP Storage Patterns)

**목표**: 견고한 프로덕션 등급의 Cloud Storage 상호작용 구현.

## 1. 재시도 정책 (필수)
GCS는 429(속도 제한) 또는 503(서비스 사용 불가) 오류가 발생할 수 있습니다. 반드시 이를 처리해야 합니다.

```python
from google.cloud import storage
from google.api_core.retry import Retry

# 견고한 재시도 정책
custom_retry = Retry(
    initial=1.0,      # 최초 1초 대기
    maximum=60.0,     # 최대 60초 대기
    multiplier=2.0,   # 실패 시 대기 시간 2배 증가
    deadline=300.0,   # 5분 후 포기
    predicate=Retry.if_exception_type(
        exceptions.ServiceUnavailable,
        exceptions.TooManyRequests,
        exceptions.InternalServerError
    )
)

def upload_file(bucket_name, source, dest):
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(dest)
    blob.upload_from_filename(source, retry=custom_retry)
```

## 2. 보안 (Security)
- **절대 금지**: 키(key)를 코드에 하드코딩하지 마십시오. `GOOGLE_APPLICATION_CREDENTIALS` 환경 변수를 사용하십시오.
- **키 무시**: `.gitignore`에 `*.json`을 추가하여 키 파일이 커밋되지 않도록 하십시오.

## 3. 대용량 파일
10MB 이상의 파일은 재개 가능한 업로드(Python 클라이언트 기본값)를 사용하되, 타임아웃이 충분한지 확인하십시오.

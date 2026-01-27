# 운영 가이드

이 문서는 배포, 환경 변수, 모니터링, 문제 해결을 위한 최소 가이드를 제공합니다.

## 환경 변수

필수:
- `GOOGLE_CLOUD_PROJECT_ID`
- `GOOGLE_API_KEY`
- `NAVER_CLIENT_ID`
- `NAVER_CLIENT_SECRET`

선택:
- `GOOGLE_CLOUD_LOCATION` (기본값: `us-central1`)
- `GOOGLE_APPLICATION_CREDENTIALS` (GCP 서비스 계정 경로)
- `GCS_BUCKET_NAME` (GCS 업로드 사용 시)
- `NOTION_API_KEY` (Notion 내보내기 사용 시)
- `NOTION_DATABASE_ID`
- `OUTPUT_DIR` (결과물 저장 경로)

## 배포/실행

- 권장 실행: `python run.py`
- 서버 실행 시 환경 변수는 OS 환경 또는 `.env`로 주입
- GCS 업로드 사용 시 서비스 계정 권한 필요

## 모니터링/로그

- 실행 로그는 Streamlit UI의 로그 뷰어와 `outputs/` 저장 경로를 참고하세요.
- 오류 메시지는 `utils/error_handler.py`에서 사용자 메시지로 매핑됩니다.

## API 쿼터/레이트 리밋

- YouTube/Naver/Gemini API는 쿼터 제한이 있습니다.
- 쿼터 초과/429 발생 시 백오프 재시도가 적용됩니다.
- 반복 조회는 TTL 캐시를 활용해 API 호출 수를 줄입니다.

## Troubleshooting

- **설정 누락 경고**: 앱 시작 시 누락된 필수 설정이 경고로 표시됩니다.
- **Notion 전송 실패**: 페이지 ID/URL 형식 및 API 키 권한을 확인하세요.
- **GCS 업로드 실패**: 서비스 계정 권한 및 버킷 접근 권한을 점검하세요.

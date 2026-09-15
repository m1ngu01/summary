# 게시 방식 변경

파일 감시·로그인 자동 실행을 제거했습니다.

- **ver1:** `python ver1/app.py` → 서재 갱신 및 GitHub 게시 버튼
- **ver2:** `.venv/Scripts/python.exe ver2/app.py` → 링크 추출·독서 HTML 생성·게시
- **단일 명령:** `python scripts/publish_library.py`
- **기존 감시 해제:** `powershell -ExecutionPolicy Bypass -File scripts/disable_auto_publish.ps1`

설치·사용 방법과 게시 범위는 [프로젝트 README](../README.md)를 참고하세요.

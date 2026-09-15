# ver1 — 완성된 HTML 게시

프로젝트 루트에서 `python ver1/app.py` 또는 `ver1/run.ps1`을 실행하세요.

`html/`에 문서를 넣고 **서재 갱신 및 GitHub 게시** 버튼을 한 번 누릅니다.
파일 감시 없이 서재 목록 생성 → HTML 커밋 → 푸시를 실행합니다.
Pages는 푸시 뒤 GitHub Actions에서 배포합니다.

독립된 실행 화면이며 서재 생성·게시 코드는 `../scripts/`를 공유합니다.
별도 Python 패키지는 필요하지 않습니다. Python(Tkinter 포함), Git, GitHub 인증이 필요합니다.
원본 TXT·코드·외부 이미지·CSS는 게시 대상에서 제외합니다.

자세한 설명은 [루트 README](../README.md)를 참고하세요.

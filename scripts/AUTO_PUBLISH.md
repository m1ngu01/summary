# HTML 자동 게시

Windows에서 다음 명령으로 설치·시작합니다. Windows 로그인 때도 자동 시작합니다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_auto_publish.ps1
```

PC가 켜져 있고 로그인한 동안 `html/` 아래 HTML의 추가·수정·삭제를 감지합니다. 마지막 변경 뒤 15초가 지나면 서재 목록을 갱신하고 관련 HTML만 커밋하여 `origin/main`에 푸시합니다. GitHub Actions가 Pages를 배포합니다. **HTML을 저장하면 공개 사이트에 반영됩니다.**

Git 인증이 미리 되어 있어야 합니다. 오류 기록은 `.auto-publish/publish.log`에 남고 60초 간격으로 재시도합니다. 원격 브랜치가 앞서 있으면 직접 동기화해야 합니다. 강제 푸시나 자동 병합은 하지 않습니다. HTML 외 이미지, CSS, 원본 TXT 및 도구 변경은 직접 커밋하세요. 푸시는 브랜치 전체를 전송하므로 기존 로컬 커밋도 함께 올라갑니다.

중지하려면 아래 명령을 실행합니다. 다시 시작하려면 설치 명령을 다시 실행하세요.

```powershell
New-Item -ItemType File -Path .auto-publish/stop -Force
```

자동 시작을 해제하려면 `Win + R` → `shell:startup`에서 `Summary Auto Publish` 바로가기를 삭제하고 중지 명령도 실행합니다. 저장소나 Python 설치 위치를 바꾸면 설치 명령을 다시 실행하세요.

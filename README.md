# Summary — 두 가지 실행 버전

완성된 HTML을 게시하는 **ver1**과 YouTube 원문을 독서 HTML로 만드는 **ver2**입니다.
한 저장소에서 실행 화면을 분리하고 `scripts/`의 서재 생성·게시 기능을 공유합니다.
`ver2/`의 프롬프트와 템플릿을 바꾸어도 ver1의 입력 방식은 바뀌지 않습니다.

| 버전 | 흐름 | 실행 |
| --- | --- | --- |
| ver1 | HTML 준비 → 게시 버튼 → 목록 생성·커밋·푸시 → Pages | `python ver1/app.py` |
| ver2 | 링크 → 추출 → 원문 편집 → HTML 생성 → 미리보기·다운로드 → 게시 버튼 | `.venv/Scripts/python.exe ver2/app.py` |

## ver1: HTML 게시

Python 3.10 이상(Tkinter 포함), Git, `origin` 원격과 `main` 브랜치가 필요합니다.
GitHub 인증과 저장소의 Settings → Pages → GitHub Actions 설정을 먼저 완료하세요.

1. `html/`에 `.html` 또는 `.htm` 파일을 넣습니다. 하위 폴더와 대소문자 확장자를 지원합니다.
2. `python ver1/app.py` 실행 후 **서재 갱신 및 GitHub 게시**를 누릅니다.
3. 루트와 `html/`의 목록을 갱신하고, HTML 변경만 커밋·푸시합니다.
4. 실제 Pages 갱신은 푸시 이후 GitHub Actions에서 진행됩니다.

명령 한 번으로 실행하려면 `python scripts/publish_library.py`를 사용합니다.
`ver1/run.ps1`도 같은 화면을 실행합니다.

**범위:** `html/`의 HTML 및 자동 생성되는 루트 `index.html`만 커밋합니다.
Pages 결과물에도 HTML과 `.nojekyll`만 포함합니다. 별도 CSS·이미지·TXT는 복사하지 않으므로,
독서 파일의 이미지와 스타일은 HTML 안에 포함하세요. 기존 Git 이력의 파일을 삭제하는 기능은 아닙니다.

Git은 파일별로 푸시할 수 없으므로 미푸시 커밋에 범위 밖 파일이 있으면 중단합니다.
앱 코드·워크플로 변경의 최초 반영은 직접 커밋·푸시한 뒤 콘텐츠 게시 버튼을 사용하세요.
관계없는 스테이징은 보존하며 원격이 앞선 경우 자동 병합·강제 푸시하지 않습니다.
푸시 실패 후 같은 버튼을 다시 누르면 기존 커밋을 재전송합니다.

## ver2: YouTube 독서 HTML

### 설치 및 실행 (PowerShell, 프로젝트 루트)

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r ver2/requirements.txt
.venv/Scripts/python.exe ver2/app.py
```

또는 설치 후 `ver2/run.ps1`을 실행합니다. 가상환경 활성화는 필요하지 않습니다.
`imageio-ffmpeg`가 음성 분할용 FFmpeg를 제공합니다. 시스템 FFmpeg가 있으면 우선 사용합니다.
PATH의 Deno 또는 Node.js를 자동으로 찾아 YouTube JavaScript 처리에 사용합니다. 다운로드가 관련 오류로 실패하면
[yt-dlp의 EJS 안내](https://github.com/yt-dlp/yt-dlp/wiki/EJS)에 따라 Deno 등을 설치하세요.
영상별 접근 제한이나 YouTube의 차단으로 추출이 실패할 수 있으며, TXT 불러오기·붙여넣기로도 진행할 수 있습니다.

### 사용 순서

1. **링크 입력 → 텍스트 추출:** 수동 자막, 자동 자막 순으로 확인합니다. 기본 언어는 `ko`입니다.
   사용 가능한 자막이 없으면 음성을 내려받아 10분씩 나누고 OpenAI 음성 인식으로 처리합니다.
2. **원문 확인·수정:** 제목과 텍스트를 직접 편집할 수 있습니다. TXT 불러오기·저장도 지원합니다.
3. **독서 HTML 생성:** API 키와 문장 교정 모델을 입력합니다. 기본값은 `gpt-4.1-mini`입니다.
4. **미리보기·HTML 다운로드:** 브라우저에서 결과를 확인하거나 원하는 위치에 단일 파일로 저장합니다.
5. **GitHub 게시:** `html/youtube-영상ID.html`과 현재 영상의 원본 TXT를 저장하고 게시합니다.
   같은 영상 ID는 같은 파일을 갱신합니다. 다른 HTML 변경도 함께 게시하며 화면에 이를 표시합니다.

API 키는 창에서만 보관하며 파일이나 생성 HTML에 저장하지 않습니다.
`OPENAI_API_KEY`, `OPENAI_TEXT_MODEL`, `OPENAI_AUDIO_MODEL` 환경변수도 사용할 수 있습니다.
음성 모델 기본값은 `whisper-1`입니다. 계정에 해당 모델 사용 권한이 필요합니다.
문장 교정은 편집 원문을, 음성 인식은 다운로드한 음성을 OpenAI API로 전송하며 사용료가 발생합니다.
자막 추출 자체는 OpenAI API를 사용하지 않습니다. 별도의 `.env` 자동 로딩은 없습니다.

### 생성 규칙

- 원문 발언·사례·논거·순서·의미·말투를 최대한 보존하고 문장을 교정합니다.
- 소설화, 새로운 대사·주장·장면 묘사, 삽화를 추가하지 않습니다.
- 실제 대화의 화자 표시를 보존하고 독백은 독백으로 유지합니다.
- 표지 → 본문 안의 클릭 가능한 목차 → 주제별 장 → 간단한 요약을 구성합니다.
- 시간 표시·타임라인·사이드바 목차를 제외합니다.
- 다크 배경, 미색 본문, 금색 포인트, 명조·고딕 전환, 글자 크기 조절을 제공합니다.
- 외부 폰트·스크립트·이미지 없이 PC·모바일에서 단일 HTML로 읽습니다.

원문을 번호가 있는 조각으로 나누어 AI 응답의 개수·순서·빈 본문·급격한 분량 변화를 검사합니다.
이는 의미 보존을 완전히 증명하는 검사가 아닙니다. 게시 전 원문과 미리보기를 비교하세요.
긴 글 처리 중 실패하면 같은 입력·모델·프롬프트로 다시 실행할 때 완료된 교정 묶음을 재사용합니다.
음성 다운로드·인식의 중간 결과는 재시작 시 재사용하지 않습니다.

### 저장 위치와 확장 지점

| 위치 | 용도 |
| --- | --- |
| `.summary/jobs/영상ID/` | 추출 원문, 편집 입력, 생성 캐시, 미리보기. Git/Pages 제외 |
| `html/youtube-영상ID.html` | 게시 버튼으로 확정한 독서 HTML |
| `원본 유튜브 요약 텍스트/youtube-영상ID.txt` | 추출 원문과 편집 입력. ver2 게시 시 현재 영상 파일만 Git 포함, Pages 제외 |
| `ver2/prompts/reading.txt` | 원문 보존·문장 교정 프롬프트 |
| `ver2/templates/reading.html` | 독서 화면 디자인과 읽기 설정 |
| `ver2/transcript.py` | URL 처리, 자막·음성 추출 |
| `ver2/reading.py` | 분할 교정, 검사, 캐시, HTML 렌더링 |
| `ver2/app.py` | 버튼과 사용자 흐름 |
| `scripts/publish_library.py` | 공통 게시 처리 |

원문·제목·URL을 수정하면 기존 생성 결과의 미리보기·다운로드·게시를 막고 재생성을 안내합니다.
작업 중에는 입력을 잠가 결과가 다른 원문과 섞이지 않도록 합니다.

## 기존 파일 감시 제거

파일 감시 루프와 자동 시작 설치 스크립트를 제거했습니다.
과거에 자동 게시를 설치했다면 한 번 실행하세요.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/disable_auto_publish.ps1
```

기존 감시 프로세스에 중지 파일로 종료를 요청하고, 이 저장소를 가리키는 시작프로그램 바로가기만 제거합니다.
진행 중인 Git 작업은 끝날 때까지 기다립니다. 호환 명령 `scripts/auto_publish.py`는 이제 한 번만 게시하고 종료합니다.

## 테스트

```powershell
python -B -m unittest discover -s scripts -p 'test_*.py' -v
python -B -m unittest discover -s ver2 -p 'test_*.py' -v
```

테스트는 임시 Git 저장소와 모의 API를 사용합니다. 실제 YouTube·OpenAI·GitHub에 게시하지 않습니다.
GitHub Actions에서도 테스트 통과 후 Pages를 빌드합니다.

API 구현 참고: [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs),
[File transcription](https://developers.openai.com/api/docs/guides/speech-to-text).

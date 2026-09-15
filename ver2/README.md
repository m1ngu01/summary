# ver2 — YouTube 독서 HTML 제작

프로젝트 루트에서 설치 후 실행하세요.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r ver2/requirements.txt
.venv/Scripts/python.exe ver2/app.py
```

링크 입력 → 텍스트 추출 → 원문 편집 → HTML 생성 → 미리보기·다운로드 → GitHub 게시.
문장 교정과 자막 없는 영상의 음성 인식에는 OpenAI API 키가 필요합니다.

추가 수정은 다음 파일에서 진행할 수 있습니다.

- `prompts/reading.txt`: 내용 보존·교정 규칙
- `templates/reading.html`: 독서 화면·글꼴·색상·읽기 설정
- `transcript.py`: 자막·음성 추출
- `reading.py`: 원문 분할·검사·HTML 생성
- `app.py`: 버튼과 입력 흐름

소설화·삽화 생성은 포함하지 않습니다.
서재 생성·게시 코드는 `../scripts/`를 공유합니다.
설치 조건·게시 범위·저장 위치는 [루트 README](../README.md)에 정리했습니다.

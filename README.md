# 영상 서재

메인 화면에서 `html/` 안의 모든 HTML 문서를 찾아 읽을 수 있는 다크모드 서재입니다. 현재 파일뿐 아니라 하위 폴더에 추가한 `.html`, `.htm` 파일도 자동으로 목록에 포함합니다. 서재 자체인 `html/index.html`은 제외합니다.

## 처음 GitHub Pages를 켤 때

1. 이 작업 폴더의 변경 사항을 GitHub 저장소의 `main` 브랜치에 커밋하고 푸시합니다.
2. 저장소 **Settings → Pages → Build and deployment → Source**를 **GitHub Actions**로 선택합니다.
3. **Actions → Build and deploy reading library → Run workflow**로 배포합니다. 이후에는 `main`에 푸시할 때마다 자동으로 갱신됩니다.
4. 배포 성공 후 `https://m1ngu01.github.io/summary/`를 열면 전체 서재가 보입니다. 별도 도메인을 설정한 경우에는 Pages 설정에 표시되는 주소를 사용합니다.

워크플로는 공식 [GitHub Pages 사용자 지정 워크플로](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) 방식을 사용합니다.

## 새 책 추가하기

- 읽을 HTML과 관련 이미지·스타일 파일을 `html/` 폴더에 넣습니다.
- 원본 텍스트는 `원본 유튜브 요약 텍스트/` 폴더에 넣습니다.
- GitHub에 커밋하고 푸시하면 배포할 때 모든 파일을 다시 조사해 목록을 만듭니다. 삭제한 HTML은 목록에서도 빠집니다.
- 제목은 HTML의 첫 `<h1>`, `<title>`, 파일명 순으로 사용합니다. `<p class="subtitle">`가 있으면 소개로 표시합니다.
- 메인 화면에서 제목, 소개, 파일명으로 검색할 수 있습니다.

## 로컬에서 보기

```sh
python scripts/build_library.py
```

실행 후 루트의 `index.html`을 브라우저로 열면 됩니다. `html/index.html`도 같은 목록으로 갱신되므로 기존 책의 ‘서재로’ 링크가 그대로 작동합니다. 목록은 정적 HTML이므로 네트워크나 JavaScript 없이도 열 수 있으며, 검색만 JavaScript를 사용합니다.

배포에서는 새 `_site/` 폴더에 메인 화면, HTML 폴더, 원본 텍스트 폴더를 복사합니다. 원본 텍스트 링크도 배포 사이트에서 열 수 있습니다. 빌드 스크립트나 Git 저장소 내부 파일은 배포하지 않습니다.

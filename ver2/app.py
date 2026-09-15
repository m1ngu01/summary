"""Version 2: explicit extract, edit, generate, download and publish steps."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from desktop import TaskWindow
from publish_library import publish
from transcript import extract, video_url
from reading import generate, render


def client_for(key):
    if not key.strip():
        raise ValueError('OpenAI API 키를 입력하거나 OPENAI_API_KEY 환경변수를 설정하세요.')
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError('ver2/requirements.txt의 패키지를 설치하세요.') from exc
    return OpenAI(api_key=key.strip(), timeout=180, max_retries=2)


class App(TaskWindow):
    def __init__(self):
        super().__init__('Summary ver2 · YouTube 독서 HTML')
        self.extracted = None
        self.generated = None
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='YouTube → 독서 HTML', font=('Malgun Gothic', 22)).pack(anchor='w')
        ttk.Label(frame, text='원문 확인 → 문장 교정 → 미리보기 → 게시', padding=(0, 6)).pack(anchor='w')
        fields = ttk.Frame(frame)
        fields.pack(fill='x', pady=8)
        fields.columnconfigure(1, weight=1)
        self.url = self.field(fields, 0, 'YouTube 링크')
        self.title_value = self.field(fields, 1, '글 제목')
        self.key = self.field(fields, 2, 'OpenAI API 키', os.getenv('OPENAI_API_KEY', ''), secret=True)
        self.model = self.field(fields, 3, '문장 교정 모델', os.getenv('OPENAI_TEXT_MODEL', 'gpt-4.1-mini'))
        self.language = self.field(fields, 4, '자막·음성 언어', 'ko')
        ttk.Label(frame, text='키는 파일에 저장하지 않습니다. HTML 생성과 자막 없는 영상의 음성 인식은 API 사용료가 발생합니다.',
                  wraplength=850).pack(anchor='w')
        top = ttk.Frame(frame)
        top.pack(fill='x', pady=5)
        self.button(top, '1. 텍스트 추출', self.extract_text)
        self.button(top, 'TXT 불러오기', self.load_text)
        self.button(top, '원문 TXT 저장', self.save_text)
        ttk.Label(frame, text='원문 확인·수정 (직접 붙여넣기도 가능)').pack(anchor='w', pady=(6, 3))
        self.editor = ScrolledText(frame, wrap='word', undo=True, font=('Malgun Gothic', 11), height=14)
        self.editor.pack(fill='both', expand=True)
        self.controls.append(self.editor)
        row = ttk.Frame(frame)
        row.pack(fill='x')
        self.button(row, '2. 독서 HTML 생성', self.generate_html)
        self.button(row, '3. 미리보기', self.preview)
        self.button(row, 'HTML 다운로드', self.download)
        self.button(row, '4. GitHub 게시', self.publish_html)
        ttk.Label(frame, text='게시 버튼은 html/의 변경된 HTML과 현재 영상의 원본 TXT를 커밋·푸시합니다.',
                  wraplength=850).pack(anchor='w', pady=4)
        ttk.Label(frame, textvariable=self.status, wraplength=850).pack(anchor='w', pady=6)

    def field(self, frame, row, label, initial='', secret=False):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', padx=(0, 16), pady=3)
        value = tk.StringVar(value=initial)
        widget = ttk.Entry(frame, textvariable=value, show='*' if secret else '')
        widget.grid(row=row, column=1, sticky='ew', pady=3)
        self.controls.append(widget)
        return value

    def inputs(self):
        ident, url = video_url(self.url.get())
        title = self.title_value.get().strip()
        text = self.editor.get('1.0', 'end-1c').strip()
        if not title or not text:
            raise ValueError('영상 링크, 제목, 원문을 입력하세요.')
        return {'id': ident, 'url': url, 'title': title, 'text': text}

    @staticmethod
    def fingerprint(data):
        return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

    def extract_text(self):
        url, key, language = self.url.get(), self.key.get(), self.language.get().strip()
        if self.editor.get('1.0', 'end-1c').strip() and not messagebox.askyesno(
                '원문 교체', '새 추출 결과로 편집 중인 원문을 교체할까요?', parent=self):
            return
        def task():
            data = extract(url, language, client_for(key) if key.strip() else None,
                           os.getenv('OPENAI_AUDIO_MODEL', 'whisper-1'), self.log)
            folder = ROOT / '.summary/jobs' / data['id']
            folder.mkdir(parents=True, exist_ok=True)
            # Preserve exact extraction separately from the user's edited input.
            stamp = self.fingerprint(data)[:16]
            (folder / f'extracted-{stamp}.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            return data
        def done(data):
            self.extracted, self.generated = data, None
            self.url.set(data['url'])
            self.title_value.set(data['title'])
            self.editor.delete('1.0', 'end')
            self.editor.insert('1.0', data['text'])
            self.status.set(f"추출 완료 ({data['method']}). 원문을 확인한 뒤 HTML을 생성하세요.")
        self.run_task(task, done)

    def load_text(self):
        path = filedialog.askopenfilename(filetypes=[('UTF-8 텍스트', '*.txt')], parent=self)
        if not path:
            return
        try:
            text = Path(path).read_text(encoding='utf-8-sig')
        except (OSError, UnicodeError) as exc:
            messagebox.showerror('읽기 실패', str(exc), parent=self)
            return
        if self.editor.get('1.0', 'end-1c').strip() and not messagebox.askyesno(
                '원문 교체', '불러온 TXT로 현재 원문을 교체할까요?', parent=self):
            return
        self.editor.delete('1.0', 'end')
        self.editor.insert('1.0', text)
        self.extracted = self.generated = None
        self.status.set('텍스트를 불러왔습니다. 영상 링크와 제목도 입력하세요.')

    def save_text(self):
        path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('텍스트', '*.txt')], parent=self)
        if path:
            try:
                Path(path).write_text(self.editor.get('1.0', 'end-1c'), encoding='utf-8')
                self.status.set('원문 TXT 저장 완료')
            except OSError as exc:
                messagebox.showerror('저장 실패', str(exc), parent=self)

    def generate_html(self):
        try:
            data = self.inputs()
            client = client_for(self.key.get())
            model = self.model.get().strip()
            if not model:
                raise ValueError('문장 교정 모델을 입력하세요.')
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror('입력 확인', str(exc), parent=self)
            return
        self.generated = None
        original = self.extracted if self.extracted and self.extracted['id'] == data['id'] else data
        def task():
            folder = ROOT / '.summary/jobs' / data['id']
            folder.mkdir(parents=True, exist_ok=True)
            fingerprint = self.fingerprint(data)
            (folder / f'input-{fingerprint}.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            document = generate(data['text'], data['title'], data['url'], client, model, folder / 'cache', self.log)
            html = render(document)
            target = folder / f'{fingerprint}.html'
            target.write_text(html, encoding='utf-8')
            return {'data': data, 'original': original, 'fingerprint': fingerprint, 'html': html, 'path': target}
        def done(result):
            self.generated = result
            self.status.set('HTML 생성 완료. 미리보기에서 원문 보존과 교정 결과를 확인하세요.')
        self.run_task(task, done)

    def current_result(self):
        if not self.generated:
            raise ValueError('독서 HTML을 먼저 생성하세요.')
        if self.generated['fingerprint'] != self.fingerprint(self.inputs()):
            raise ValueError('원문·제목·링크가 변경되었습니다. HTML을 다시 생성하세요.')
        return self.generated

    def preview(self):
        try:
            result = self.current_result()
            webbrowser.open(result['path'].resolve().as_uri())
        except ValueError as exc:
            messagebox.showerror('미리보기', str(exc), parent=self)

    def download(self):
        try:
            result = self.current_result()
        except ValueError as exc:
            messagebox.showerror('다운로드', str(exc), parent=self)
            return
        path = filedialog.asksaveasfilename(initialfile=result['data']['id'] + '.html',
                                          defaultextension='.html', filetypes=[('HTML', '*.html')], parent=self)
        if path:
            try:
                Path(path).write_text(result['html'], encoding='utf-8')
                self.status.set('단일 HTML 파일 저장 완료')
            except OSError as exc:
                messagebox.showerror('저장 실패', str(exc), parent=self)

    def publish_html(self):
        try:
            result = self.current_result()
        except ValueError as exc:
            messagebox.showerror('게시', str(exc), parent=self)
            return
        def task():
            data, original = result['data'], result['original']
            html_path = ROOT / 'html' / f"youtube-{data['id']}.html"
            raw_path = ROOT / '원본 유튜브 요약 텍스트' / f"youtube-{data['id']}.txt"
            def prepare():
                html_path.parent.mkdir(parents=True, exist_ok=True)
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                # Save under the shared publish lock, after Git preflight checks.
                # Same video ID updates the same file; titles never become paths.
                html_path.write_text(result['html'], encoding='utf-8')
                raw_path.write_text(f"제목: {data['title']}\n출처: {data['url']}\n\n[추출 원문]\n{original['text']}\n\n[편집 입력]\n{data['text']}\n", encoding='utf-8')
            return publish(ROOT, [raw_path.relative_to(ROOT).as_posix()], self.log, prepare)
        self.run_task(task, lambda count: self.status.set(f'게시 처리 완료 · 서재 {count}편. 배포 상태는 GitHub Actions에서 확인하세요.'))


if __name__ == '__main__':
    App().mainloop()

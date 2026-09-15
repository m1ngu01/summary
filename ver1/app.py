"""Version 1: one button, one publish run."""
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from desktop import TaskWindow
from publish_library import publish


class App(TaskWindow):
    def __init__(self):
        super().__init__('Summary ver1 · HTML 게시')
        self.geometry('760x560')
        frame = ttk.Frame(self, padding=28)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='HTML 서재 게시', font=('Malgun Gothic', 24)).pack(anchor='w', pady=16)
        ttk.Label(frame, text='html/에 HTML 파일을 넣은 뒤 아래 버튼을 누르세요.\n\n'
                  '서재 목록 갱신 → 관련 HTML 커밋 → GitHub 푸시 → Pages 배포\n'
                  '원본 TXT와 도구 코드는 게시 대상에 포함하지 않습니다.\n'
                  'HTML은 이미지·스타일을 내장한 단일 파일을 권장합니다.',
                  justify='left').pack(anchor='w', pady=16)
        row = ttk.Frame(frame)
        row.pack(anchor='w')
        self.button(row, '서재 갱신 및 GitHub 게시', self.start)
        self.history = tk.Text(frame, height=12, wrap='word', state='disabled')
        self.history.pack(fill='both', expand=True, pady=16)
        ttk.Label(frame, textvariable=self.status, wraplength=650).pack(anchor='w')

    def start(self):
        lines = []
        def log(text):
            lines.append(text)
            self.log(text)
        def done(count):
            self.history.configure(state='normal')
            self.history.insert('end', '\n'.join(lines) + f'\n서재: {count}편\n\n')
            self.history.configure(state='disabled')
            self.history.see('end')
        self.run_task(lambda: publish(log=log), done)


if __name__ == '__main__':
    App().mainloop()

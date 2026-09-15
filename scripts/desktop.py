"""Tk worker helper; all widget updates run on the main thread."""
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox


class TaskWindow(tk.Tk):
    def __init__(self, title):
        super().__init__()
        self.title(title)
        self.geometry('940x760')
        self.minsize(680, 560)
        self.events = queue.Queue()
        self.busy = False
        self.controls = []
        self.status = tk.StringVar(value='준비되었습니다.')
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.poll_id = self.after(100, self.poll)

    def log(self, text):
        self.events.put(('log', text))

    def run_task(self, task, complete=lambda result: None):
        if self.busy:
            return
        self.busy = True
        for widget in self.controls:
            widget.configure(state='disabled')
        self.status.set('처리 중…')
        def worker():
            try:
                self.events.put(('done', (complete, task())))
            except Exception as exc:
                self.events.put(('error', str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        while not self.events.empty():
            kind, value = self.events.get()
            if kind == 'log':
                self.status.set(value)
            else:
                self.busy = False
                for widget in self.controls:
                    widget.configure(state='normal')
                if kind == 'error':
                    self.status.set('실패 — 입력과 설정을 확인하고 다시 시도하세요.')
                    messagebox.showerror('작업 실패', value, parent=self)
                else:
                    callback, result = value
                    try:
                        callback(result)
                    except Exception as exc:
                        self.status.set('결과 처리 실패')
                        messagebox.showerror('작업 실패', str(exc), parent=self)
        self.poll_id = self.after(100, self.poll)

    def destroy(self):
        self.after_cancel(self.poll_id)
        super().destroy()

    def close(self):
        if self.busy:
            messagebox.showinfo('처리 중', '현재 작업이 끝난 뒤 창을 닫아 주세요.', parent=self)
        else:
            self.destroy()

    def button(self, parent, text, command):
        button = ttk.Button(parent, text=text, command=command)
        button.pack(side='left', padx=4, pady=6)
        self.controls.append(button)
        return button

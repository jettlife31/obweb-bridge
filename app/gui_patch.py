"""Patch tab shared by the Windows and Linux desktop GUI."""
from pathlib import Path
import queue
import threading
from tkinter import filedialog, ttk
import tkinter as tk

import game_patch


class PatchTab:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent, padding=16)
        self.root = parent.winfo_toplevel()
        self.busy = False
        self.closing = False
        self.game = None
        self.source = None
        self.cancel = threading.Event()
        self.events = queue.Queue()
        self.text = tk.StringVar(value='No file selected')
        self.hash_text = tk.StringVar()
        ttk.Label(self.frame, text='Patch your game ISO', font=('TkDefaultFont', 11, 'bold')).pack(anchor='w')
        ttk.Label(self.frame, text='Select an original, unmodified USA ISO: Outbreak v2.00 or File #2.\nThe original is preserved. Only an exact SHA-256 match can be patched.', wraplength=760).pack(anchor='w', pady=12)
        self.browse = ttk.Button(self.frame, text='Browse…', command=self.select)
        self.browse.pack(anchor='e')
        ttk.Label(self.frame, textvariable=self.text, wraplength=760).pack(anchor='w', fill='x', pady=12)
        ttk.Label(self.frame, textvariable=self.hash_text, wraplength=760).pack(anchor='w', fill='x')
        self.progress = ttk.Progressbar(self.frame, maximum=100)
        self.progress.pack(fill='x', pady=16)
        actions = ttk.Frame(self.frame)
        actions.pack(anchor='w')
        self.apply = ttk.Button(actions, text='Apply patch', command=self.patch, state='disabled')
        self.apply.pack(side='left')
        self.cancel_button = ttk.Button(actions, text='Cancel', command=self.cancel.set, state='disabled')
        self.cancel_button.pack(side='left', padx=8)
        self.root.after(100, self.pump)

    def start(self, work):
        self.busy = True
        self.cancel.clear()
        self.browse.configure(state='disabled')
        self.apply.configure(state='disabled')
        self.cancel_button.configure(state='normal')
        self.progress['value'] = 0
        self.text.set('Starting…')

        def report(stage, fraction):
            self.events.put(('progress', (stage, fraction)))

        def run():
            try:
                result = work(report)
                self.events.put(('done', result))
            except game_patch.PatchError as error:
                self.events.put(('error', str(error)))
            except FileExistsError:
                self.events.put(('error', 'The output file already exists. Choose a new filename; existing files are preserved.'))
            except OSError as error:
                self.events.put(('error', f'Could not read or write the ISO (OS error {error.errno}). Check permissions and free disk space.'))
            except Exception:
                self.events.put(('error', 'Patching failed unexpectedly. The original ISO was preserved.'))
        threading.Thread(target=run, daemon=True).start()

    def select(self):
        if self.closing or self.busy:
            return
        filename = filedialog.askopenfilename(parent=self.frame, title='Select original game ISO', filetypes=[('ISO image', '*.iso'), ('All files', '*')])
        if not filename:
            return
        self.source = Path(filename)
        self.game = None
        self.hash_text.set('')
        self.start(lambda report: ('identified', game_patch.inspect_iso(self.source, report, self.cancel)))

    def patch(self):
        if self.closing or self.busy or self.game is None:
            return
        filename = filedialog.asksaveasfilename(parent=self.frame, title='Save patched ISO', initialdir=str(self.source.parent), initialfile=self.source.stem + ' - Outbreak Web.iso', defaultextension='.iso', filetypes=[('ISO image', '*.iso')])
        if not filename:
            return
        self.start(lambda report: ('patched', game_patch.apply_patch(self.source, filename, self.game, report, self.cancel)))

    def pump(self):
        for _ in range(100):
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == 'progress':
                stage, fraction = value
                self.text.set(f'{stage} — {fraction:.0%}')
                self.progress['value'] = fraction * 100
            else:
                self.busy = False
                self.browse.configure(state='disabled' if self.closing else 'normal')
                self.cancel_button.configure(state='disabled')
                if kind == 'error':
                    self.text.set(value)
                    # A failed recheck requires selecting and hashing again.
                    self.game = None
                elif value[0] == 'identified':
                    self.game = value[1]
                    self.text.set(f'{self.game.title} — original ISO verified.\n{self.source}')
                    self.hash_text.set('Original SHA-256: ' + self.game.original)
                else:
                    self.text.set(f'Patch complete. Saved ISO SHA-256 verified.\n{value[1]}')
                    self.hash_text.set('Patched SHA-256: ' + self.game.patched)
                self.apply.configure(state='normal' if self.game is not None and not self.closing else 'disabled')
        self.root.after(100, self.pump)

    def close(self):
        self.closing = True
        self.cancel.set()
        for button in (self.browse, self.apply, self.cancel_button):
            button.configure(state='disabled')

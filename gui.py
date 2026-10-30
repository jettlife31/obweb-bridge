#!/usr/bin/env python3
"""One desktop interface for Windows and Linux; no GUI is needed by containers."""
import collections
from datetime import datetime
import importlib.util
import os
from pathlib import Path
import platform
import queue
import shutil
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import webbrowser

import gui_accounts
from gui_backend import BridgeController, ROOT
import login_web as login


class BridgeApp:
    def __init__(self, root):
        self.root = root
        self.events = queue.Queue()
        self.controller = BridgeController(self.events.put)
        self.identity = None
        self.account_busy = False
        self.closing = False
        self.history = collections.deque(maxlen=500)
        self.interface_options = {}
        self.status = tk.StringVar(value='Stopped')
        self.mode = tk.StringVar(value='ethernet')
        self.interface = tk.StringVar()
        self.adapter = tk.StringVar()
        self.account_mode = tk.StringVar(value='saved')
        self.account_value = tk.StringVar()
        self.generate = tk.BooleanVar(value=False)
        self.details = tk.StringVar(value='Prepare an account before starting the bridge.')
        self.instructions = tk.StringVar()
        self.root.title('Outbreak Web Bridge')
        self.root.geometry('900x760')
        self.root.minsize(760, 640)
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        style = ttk.Style(root)
        style.theme_use('clam')
        font = 'Segoe UI' if sys.platform == 'win32' else 'DejaVu Sans'
        style.configure('.', font=(font, 10), background='#f4f6fa', foreground='#17263c')
        style.configure('TNotebook', borderwidth=0)
        style.configure('TNotebook.Tab', padding=(12, 8))
        style.map('TNotebook.Tab', background=[('selected', '#ffffff')])
        style.configure('Title.TLabel', font=(font, 20, 'bold'))
        style.configure('Status.TLabel', font=(font, 11, 'bold'), foreground='#2459a6')
        style.configure('TButton', padding=(12, 7))
        style.configure('Start.TButton', background='#2459a6', foreground='white')
        style.map('Start.TButton', background=[('active', '#194681'), ('disabled', '#dbe2ec')],
                  foreground=[('disabled', '#6d7886')])
        frame = ttk.Frame(root, padding=20)
        frame.pack(fill='both', expand=True)
        heading = ttk.Frame(frame)
        heading.pack(fill='x')
        ttk.Label(heading, text='Outbreak Web Bridge', style='Title.TLabel').pack(side='left')
        ttk.Label(heading, textvariable=self.status, style='Status.TLabel').pack(side='right')
        ttk.Label(frame, text='Connect your emulator or console. Keep this window open while playing.').pack(anchor='w', pady=(6, 16))
        tabs = ttk.Notebook(frame)
        tabs.pack(fill='both', expand=True)
        self.connection_tab = ttk.Frame(tabs, padding=16)
        self.account_tab = ttk.Frame(tabs, padding=16)
        self.setup_tab = ttk.Frame(tabs, padding=16)
        tabs.add(self.connection_tab, text='Connection')
        tabs.add(self.account_tab, text='Account & memory cards')
        tabs.add(self.setup_tab, text='Setup')
        self.tabs = tabs
        self._connection_widgets()
        self._account_widgets()
        self._setup_widgets()
        bar = ttk.Frame(frame)
        bar.pack(fill='x', pady=(12, 8))
        self.start_button = ttk.Button(bar, text='Start bridge', command=self.start, style='Start.TButton')
        self.start_button.pack(side='left')
        self.stop_button = ttk.Button(bar, text='Stop', command=self.stop, state='disabled')
        self.stop_button.pack(side='left', padx=8)
        ttk.Button(bar, text='Copy diagnostic report', command=self.copy_report).pack(side='right')
        self.log = scrolledtext.ScrolledText(frame, height=8, wrap='word', state='disabled', font=('TkFixedFont', 9))
        self.log.pack(fill='x')
        self.account_value.trace_add('write', self._invalidate_identity)
        self.refresh_accounts()
        self._account_changed()
        self._mode_changed()
        self.root.after(100, self._pump)
        self.check_setup()

    def _connection_widgets(self):
        tab = self.connection_tab
        ttk.Label(tab, text='Where is the game running?').pack(anchor='w')
        self.ethernet_radio = ttk.Radiobutton(tab, text='PCSX2 on this computer', value='ethernet', variable=self.mode, command=self._mode_changed)
        self.ethernet_radio.pack(anchor='w', pady=(8, 3))
        self.gateway_radio = ttk.Radiobutton(tab, text='Another device on the LAN (Android, PS2 or another PC)', value='gateway', variable=self.mode, command=self._mode_changed)
        self.gateway_radio.pack(anchor='w')
        if sys.platform != 'linux':
            self.gateway_radio.configure(state='disabled')
            ttk.Label(tab, text='LAN gateway hosting currently requires Linux. Local PCSX2 works on Windows and Linux.').pack(anchor='w', pady=5)
        self.lan_frame = ttk.Frame(tab)
        ttk.Label(self.lan_frame, text='Client LAN interface:').pack(anchor='w')
        line = ttk.Frame(self.lan_frame)
        line.pack(fill='x', pady=4)
        self.interface_box = ttk.Combobox(line, textvariable=self.interface, state='readonly')
        self.interface_box.pack(side='left', fill='x', expand=True)
        self.refresh_button = ttk.Button(line, text='Refresh', command=self.refresh_interfaces)
        self.refresh_button.pack(side='left', padx=(8, 0))
        self.adapter_frame = ttk.Frame(tab)
        ttk.Label(self.adapter_frame, text='Existing dedicated TAP name (optional):').pack(anchor='w')
        self.adapter_entry = ttk.Entry(self.adapter_frame, textvariable=self.adapter)
        self.adapter_entry.pack(fill='x', pady=4)
        self.config_controls = [self.ethernet_radio, self.gateway_radio, self.adapter_entry, self.refresh_button]
        ttk.Separator(tab).pack(fill='x', pady=14)
        ttk.Label(tab, textvariable=self.instructions, wraplength=790, justify='left').pack(anchor='w', fill='x')
        ttk.Label(tab, textvariable=self.details, wraplength=790, justify='left').pack(anchor='w', fill='x', pady=14)
        ttk.Button(tab, text='Open setup guide', command=self.open_guide).pack(anchor='w')

    def _account_widgets(self):
        tab = self.account_tab
        row = ttk.Frame(tab)
        row.pack(fill='x')
        self.account_radios = []
        for title, mode in [('Saved account', 'saved'), ('New account', 'new'), ('Import REO1 code', 'import')]:
            widget = ttk.Radiobutton(row, text=title, value=mode, variable=self.account_mode, command=self._account_changed)
            widget.pack(side='left', padx=(0, 16))
            self.account_radios.append(widget)
        self.input_label = ttk.Label(tab, text='Account:')
        self.input_label.pack(anchor='w', pady=(14, 4))
        self.saved_box = ttk.Combobox(tab, textvariable=self.account_value, state='readonly')
        self.account_entry = ttk.Entry(tab, textvariable=self.account_value)
        self.generate_box = ttk.Checkbutton(tab, text='Generate memory cards when importing this account', variable=self.generate)
        self.prepare_button = ttk.Button(tab, text='Prepare account', command=self.prepare_account)
        self.prepare_button.pack(anchor='w', pady=10)
        ttk.Label(tab, text='These credentials are private. They are excluded from the diagnostic report.').pack(anchor='w')
        self.credential_fields = {}
        for title, key in [('Username', 'name'), ('Game password', 'password'), ('REO1 transfer code', 'code')]:
            line = ttk.Frame(tab)
            line.pack(fill='x', pady=3)
            ttk.Label(line, text=title, width=19).pack(side='left')
            value = tk.StringVar()
            ttk.Entry(line, textvariable=value, state='readonly').pack(side='left', fill='x', expand=True)
            ttk.Button(line, text='Copy', command=lambda k=key: self.copy_credential(k)).pack(side='left', padx=(8, 0))
            self.credential_fields[key] = value
        self.card_text = tk.StringVar(value='No memory cards selected.')
        ttk.Label(tab, textvariable=self.card_text, wraplength=770).pack(anchor='w', pady=8)
        ttk.Button(tab, text='Open memory-card folder', command=self.open_cards).pack(anchor='w')

    def _setup_widgets(self):
        tab = self.setup_tab
        ttk.Label(tab, text='Install dependencies before starting the bridge.', font=('TkDefaultFont', 11, 'bold')).pack(anchor='w')
        self.setup_text = tk.StringVar(value='Checking local dependencies…')
        ttk.Label(tab, textvariable=self.setup_text, wraplength=790, justify='left').pack(anchor='w', pady=14)
        links = [('Python', 'https://www.python.org/downloads/')]
        if sys.platform == 'win32':
            links += [('Npcap (separate installation)', 'https://npcap.com/#download'),
                      ('OpenVPN Community — not Connect', 'https://openvpn.net/community/')]
        for label, url in links:
            ttk.Button(tab, text=label, command=lambda u=url: webbrowser.open(u)).pack(anchor='w', pady=3)
        ttk.Button(tab, text='Check again', command=self.check_setup).pack(anchor='w', pady=10)

    def refresh_accounts(self):
        try:
            state = login.load_state(login.state_path())
            names = sorted(state['identities'])
        except (OSError, ValueError):
            state, names = {}, []
            self.events.put({'type': 'error', 'message': 'Could not read saved accounts. Check the local account state file.'})
        self.saved_box.configure(values=names)
        if names:
            self.account_value.set(state.get('last_name') if state.get('last_name') in names else names[0])
        else:
            self.account_mode.set('new')
            self.account_value.set('')

    def _account_changed(self):
        self.identity = None
        for value in self.credential_fields.values():
            value.set('')
        self.card_text.set('No memory cards selected.')
        self.saved_box.pack_forget()
        self.account_entry.pack_forget()
        self.generate_box.pack_forget()
        mode = self.account_mode.get()
        self.input_label.configure(text='Complete REO1 transfer code:' if mode == 'import' else 'Username:')
        widget = self.saved_box if mode == 'saved' else self.account_entry
        widget.pack(after=self.input_label, fill='x', pady=4)
        if mode == 'saved':
            values = self.saved_box.cget('values')
            if self.account_value.get() not in values:
                self.account_value.set(values[0] if values else '')
        else:
            self.account_value.set('')
        if mode == 'import':
            self.generate_box.pack(after=widget, anchor='w', pady=4)

    def _invalidate_identity(self, *_):
        if self.identity is not None:
            self.identity = None
            for value in self.credential_fields.values():
                value.set('')
            self.card_text.set('No memory cards selected.')
            self.details.set('Prepare the selected account before starting the bridge.')
            self.status.set('Stopped')

    def _mode_changed(self):
        self.lan_frame.pack_forget()
        self.adapter_frame.pack_forget()
        if self.mode.get() == 'gateway':
            self.lan_frame.pack(after=self.gateway_radio, fill='x', pady=10)
            self.instructions.set('Clients use this computer as their gateway and DNS. Keep the existing LAN setup on the bridge computer. The client must share the LAN.')
            self.refresh_interfaces()
        else:
            if sys.platform == 'win32':
                self.adapter_frame.pack(after=self.gateway_radio, fill='x', pady=10)
            self.instructions.set('After READY, open PCSX2: Ethernet enabled → PCAP Switched → obw-pcsx2. Disable Intercept DHCP; use automatic DNS and a new automatic in-game network profile.')

    def prepare_account(self):
        if self.account_busy or self.controller.active:
            return
        mode, value, generate = self.account_mode.get(), self.account_value.get(), self.generate.get()
        self.account_busy = True
        self._account_controls(False)
        self.status.set('Preparing account…')
        def work():
            try:
                result = gui_accounts.prepare_account(mode, value, generate)
                self.events.put({'type': 'account', 'identity': result})
            except Exception as error:
                detail = str(error) if type(error) is ValueError else f'Account setup failed ({type(error).__name__}). Retry or import your existing REO1 code.'
                self.events.put({'type': 'account_error', 'message': detail})
        threading.Thread(target=work, daemon=True).start()

    def refresh_interfaces(self):
        def work():
            try:
                from container_interfaces import interfaces
                choices = [(f'{name} — {ip}/{prefix}', name, ip) for name, addresses in interfaces() for ip, prefix in addresses]
                self.events.put({'type': 'interfaces', 'choices': choices})
            except Exception:
                self.events.put({'type': 'error', 'message': 'Could not list LAN interfaces. Install iproute2 and check the Setup tab.'})
        threading.Thread(target=work, daemon=True).start()

    def check_setup(self):
        def work():
            lines = [f'Python: {platform.python_version()}',
                     'WebSocket library: ' + ('installed' if importlib.util.find_spec('websockets') else 'missing — run the GUI launcher')]
            if sys.platform == 'win32':
                system = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32'
                lines.append('Npcap: ' + ('installed' if (system / 'Npcap/wpcap.dll').is_file() else 'not found — install Npcap separately from the official link below'))
                from ethernet_adapter import locate_tapctl
                lines.append('OpenVPN tapctl: ' + ('found' if locate_tapctl() else 'not found automatically — install Community or locate tapctl.exe when asked'))
                lines.append('Network setup requests Administrator approval when you press Start.')
            else:
                for name in ('ip', 'nft', 'sysctl', 'pkexec'):
                    lines.append(f'{name}: ' + ('installed' if shutil.which(name) else 'missing'))
                lines.append('TUN/TAP: ' + ('available' if Path('/dev/net/tun').exists() else 'missing /dev/net/tun'))
                lines.append('On Debian/Ubuntu: sudo apt install python3-venv python3-tk iproute2 nftables procps policykit-1')
            self.events.put({'type': 'setup', 'text': '\n'.join(lines)})
        threading.Thread(target=work, daemon=True).start()

    def start(self):
        if self.controller.active or self.account_busy:
            return
        if not self.identity:
            self.tabs.select(self.account_tab)
            messagebox.showinfo('Prepare account', 'Create, import or prepare a saved account before starting.', parent=self.root)
            return
        config = {'mode': self.mode.get()}
        if config['mode'] == 'gateway':
            choice = self.interface_options.get(self.interface.get())
            if not choice:
                messagebox.showerror('LAN interface', 'Select the interface connected to your client LAN.', parent=self.root)
                return
            config['interface'], config['lan_ip'] = choice
        elif sys.platform == 'win32':
            config['adapter'] = self.adapter.get().strip()
        self._controls(True)
        self.status.set('Starting…')
        self._append('Starting network setup. Account credentials stay in this window.')
        self.controller.start(config)

    def stop(self):
        self.status.set('Stopping and cleaning up…')
        self.stop_button.configure(state='disabled')
        self.controller.stop()

    def _controls(self, running):
        self.start_button.configure(state='disabled' if running else 'normal')
        self.stop_button.configure(state='normal' if running else 'disabled')
        self._account_controls(not running and not self.account_busy)
        for widget in self.config_controls + self.account_radios:
            widget.configure(state='disabled' if running else 'normal')
        self.interface_box.configure(state='disabled' if running else 'readonly')
        if sys.platform != 'linux':
            self.gateway_radio.configure(state='disabled')

    def _account_controls(self, enabled):
        state = 'normal' if enabled else 'disabled'
        for widget in self.account_radios + [self.account_entry, self.generate_box, self.prepare_button]:
            widget.configure(state=state)
        self.saved_box.configure(state='readonly' if enabled else 'disabled')

    def _append(self, line):
        if self.identity:
            for key in ('password', 'code'):
                line = line.replace(self.identity[key], '[private]')
        line = str(line)[:8000]
        if not line.startswith('['):
            line = f'[{datetime.now().astimezone().isoformat(timespec="seconds")}] {line}'
        self.history.append(line)
        self.log.configure(state='normal')
        self.log.insert('end', line + '\n')
        if int(self.log.index('end-1c').split('.')[0]) > 600:
            self.log.delete('1.0', '100.0')
        self.log.see('end')
        self.log.configure(state='disabled')

    def _pump(self):
        for _ in range(100):
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            kind = event['type']
            if kind == 'log':
                line = event['line']
                self._append(line)
                if 'READY:' in line:
                    self.status.set('Ready')
                elif 'Tunnel offline;' in line:
                    self.status.set('Reconnecting…')
            elif kind == 'status':
                self.status.set(event['message'])
            elif kind == 'plan':
                plan = event['plan']
                self.details.set(f'Client gateway and DNS: {plan["linux_ip"]}\nClient LAN: {plan["client_network"]}')
            elif kind in ('account', 'account_error'):
                self.account_busy = False
                self._account_controls(True)
                if kind == 'account':
                    self.identity = event['identity']
                    names = set(self.saved_box.cget('values'))
                    names.add(self.identity['name'])
                    self.saved_box.configure(values=sorted(names))
                    for key, field in self.credential_fields.items():
                        field.set(self.identity[key])
                    self.card_text.set('\n'.join('Memory card: ' + p for p in self.identity['cards']) or 'Use your existing or exported memory card.')
                    self.details.set('Account prepared. Select the matching memory card in the emulator, then start the bridge.')
                    self.status.set('Account ready')
                else:
                    self.identity = None
                    self.status.set('Account setup failed')
                    if not self.closing:
                        messagebox.showerror('Account', event['message'], parent=self.root)
            elif kind == 'interfaces':
                self.interface_options = {label: (name, ip) for label, name, ip in event['choices']}
                self.interface_box.configure(values=list(self.interface_options))
                if self.interface.get() not in self.interface_options:
                    self.interface.set(next(iter(self.interface_options), ''))
            elif kind == 'setup':
                self.setup_text.set(event['text'])
            elif kind == 'prompt':
                path = '' if self.closing else filedialog.askopenfilename(parent=self.root, title='Locate OpenVPN tapctl.exe', filetypes=[('tapctl.exe', 'tapctl.exe')])
                self.controller.send({'type': 'input', 'value': path})
            elif kind == 'error':
                self.status.set('Setup failed')
                self._append(event['message'])
                if not self.closing:
                    messagebox.showerror('Bridge', event['message'], parent=self.root)
            elif kind == 'stopped':
                self.status.set('Stopped')
            elif kind == 'finished':
                self._controls(False)
                if self.status.get() not in ('Setup failed',):
                    self.status.set('Stopped')
                self._append('Network worker exited.')
        if self.closing and not self.controller.active and not self.account_busy:
            self.root.destroy()
            return
        self.root.after(100, self._pump)

    def copy_credential(self, key):
        if self.identity:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.identity[key])

    def copy_report(self):
        report = f'Outbreak Web Bridge\nOS: {platform.system()} {platform.release()}\nPython: {platform.python_version()}\nMode: {self.mode.get()}\nStatus: {self.status.get()}\n\n' + '\n'.join(self.history)
        self.root.clipboard_clear()
        self.root.clipboard_append(report)

    def open_cards(self):
        folder = login.generated_card_directory()
        if not folder.is_dir():
            messagebox.showinfo('Memory cards', 'No generated memory-card folder exists yet.', parent=self.root)
            return
        webbrowser.open(folder.resolve().as_uri())

    def open_guide(self):
        page = ('windows' if sys.platform == 'win32' else 'linux') if self.mode.get() == 'ethernet' else 'lan'
        webbrowser.open(f'https://github.com/zenaror/obweb-bridge/blob/feature/shared-desktop-gui/docs/en/{page}.md')

    def close(self):
        self.closing = True
        if self.controller.active:
            self.stop()
        elif self.account_busy:
            self.status.set('Finishing account setup before closing…')
        else:
            self.root.destroy()


def main():
    if sys.platform not in ('linux', 'win32'):
        raise SystemExit('Desktop mode supports Windows and Linux.')
    root = tk.Tk()
    BridgeApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()

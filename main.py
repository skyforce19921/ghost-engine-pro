from kivy.config import Config
Config.set('graphics', 'maxfps', '120')

from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import ThreeLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.clock import Clock
from kivy.utils import platform
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
import requests
import threading
import hashlib
import urllib.parse
import random
import time
import bencode
import os
import string
import sqlite3
import json
import socket
import struct
import pytz
import datetime

CLIENT_MASKS = {
    "qBittorrent": {
        "qBit 5.1.4": {"ua": "qBittorrent/5.1.4", "prefix": "-qB5140-"},
        "qBit 5.0.1": {"ua": "qBittorrent/5.0.1", "prefix": "-qB5010-"},
        "qBit 4.6.4": {"ua": "qBittorrent/4.6.4", "prefix": "-qB4640-"},
    },
    "Transmission": {
        "Transmission 4.0.5": {"ua": "Transmission/4.0.5", "prefix": "-TR4050-"},
        "Transmission 3.00": {"ua": "Transmission/3.00", "prefix": "-TR3000-"}
    },
    "Deluge": {
        "Deluge 2.1.1": {"ua": "Deluge/2.1.1", "prefix": "-DE2110-"},
    }
}

KV = '''
<FileButton@Button>:
    filename: ''
    is_dir: False
    text_size: self.size
    halign: 'left'
    valign: 'middle'
    background_normal: ''
    background_color: 0.12, 0.15, 0.18, 1
    color: 0.9, 0.9, 0.9, 1
    markup: True
    shorten: True
    shorten_from: 'right'
    padding_x: dp(15)
    on_release: app.on_file_click(self.filename, self.is_dir)

ScreenManager:
    MainScreen:
    DetailScreen:

<MainScreen>:
    name: 'main'
    MDFloatLayout:
        MDBoxLayout:
            orientation: 'vertical'
            MDTopAppBar:
                title: "Ghost Engine PRO"
                elevation: 4
                md_bg_color: app.theme_cls.primary_color
                specific_text_color: 1, 1, 1, 1
            MDScrollView:
                MDList:
                    id: active_tasks_list
        MDFloatingActionButton:
            icon: "plus"
            md_bg_color: app.theme_cls.accent_color
            pos_hint: {"center_x": .85, "center_y": .1}
            on_release: app.add_torrent_dialog()

<DetailScreen>:
    name: 'detail'
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "Live Tracker"
            left_action_items: [["arrow-left", lambda x: app.go_back()]]
            elevation: 4
            md_bg_color: app.theme_cls.primary_color
            specific_text_color: 1, 1, 1, 1
        MDScrollView:
            MDBoxLayout:
                orientation: 'vertical'
                padding: "16dp"
                spacing: "16dp"
                size_hint_y: None
                height: self.minimum_height

                MDCard:
                    orientation: "vertical"
                    padding: "16dp"
                    spacing: "10dp"
                    size_hint_y: None
                    height: "380dp"
                    elevation: 2
                    md_bg_color: 0.1, 0.1, 0.1, 1

                    MDLabel:
                        id: detail_name
                        text: "Awaiting Payload..."
                        font_style: "Subtitle1"
                        bold: True
                    MDLabel:
                        text: "Task By Vish ( Autonomous Mobile Node )"
                        theme_text_color: "Custom"
                        text_color: 0.4, 0.6, 1, 1
                        font_style: "Caption"
                    
                    MDSeparator:

                    MDLabel:
                        id: detail_identity
                        text: "|- Identity -> Standby"
                    
                    MDBoxLayout:
                        orientation: "horizontal"
                        size_hint_y: None
                        height: "20dp"
                        MDLabel:
                            text: "|- ["
                            size_hint_x: None
                            width: "20dp"
                        MDProgressBar:
                            id: progress_bar
                            value: 0
                            color: app.theme_cls.primary_color
                        MDLabel:
                            id: progress_text
                            text: "]  0.0%"
                            size_hint_x: None
                            width: "60dp"

                    MDLabel:
                        id: detail_uploaded
                        text: "|- Uploaded -> 0.00 MB / 0.00 MB | Ratio -> 0.00"
                    MDLabel:
                        id: status_label
                        text: "|- Status -> 💤 Sleeping"
                    MDLabel:
                        id: speed_label
                        text: "|- Speed -> 0 KB/s"
                        theme_text_color: "Custom"
                        text_color: 0, 1, 0.5, 1
                    MDLabel:
                        id: detail_announce
                        text: "|- Announce -> Standby"
                    MDLabel:
                        id: detail_peers
                        text: "\\- Seeders -> 0 | Leechers -> 0"

                MDBoxLayout:
                    orientation: "horizontal"
                    spacing: "15dp"
                    size_hint_y: None
                    height: "50dp"
                    MDRaisedButton:
                        id: btn_start
                        text: "Start"
                        on_release: app.toggle_seed()
                    MDFlatButton:
                        text: "Delete"
                        theme_text_color: "Custom"
                        text_color: 1, 0.3, 0.3, 1
                        on_release: app.delete_current_task()
'''

class MainScreen(MDScreen): pass
class DetailScreen(MDScreen): pass

class Database:
    def __init__(self, path):
        self.path = path
        with sqlite3.connect(self.path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS tasks (
                info_hash TEXT PRIMARY KEY, name TEXT, peer_id TEXT, uploaded INTEGER DEFAULT 0,
                tracker_url TEXT, leechers INTEGER DEFAULT 0, key TEXT, target_size_mb REAL DEFAULT 0,
                port INTEGER DEFAULT 0, identity_key TEXT, speed_min REAL, speed_max REAL, running INTEGER DEFAULT 1
            )''')
            conn.commit()

    def add_task(self, info_hash, name, peer_id, tracker_url, key, target_size_mb, port, identity_key, s_min, s_max):
        with sqlite3.connect(self.path) as conn:
            conn.execute('''INSERT INTO tasks (info_hash, name, peer_id, tracker_url, key, target_size_mb, port, identity_key, speed_min, speed_max)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(info_hash) DO NOTHING''',
                (info_hash, name, peer_id, tracker_url, key, target_size_mb, port, identity_key, s_min, s_max))
            conn.commit()

    def update_stats(self, info_hash, uploaded, leechers):
        with sqlite3.connect(self.path) as conn:
            conn.execute('UPDATE tasks SET uploaded = ?, leechers = ? WHERE info_hash = ?', (uploaded, leechers, info_hash))
            conn.commit()
            
    def update_running(self, info_hash, running_int):
        with sqlite3.connect(self.path) as conn:
            conn.execute('UPDATE tasks SET running = ? WHERE info_hash = ?', (running_int, info_hash))
            conn.commit()

    def get_tasks(self):
        with sqlite3.connect(self.path) as conn: return conn.execute('SELECT * FROM tasks').fetchall()

    def remove_task(self, info_hash):
        with sqlite3.connect(self.path) as conn:
            conn.execute('DELETE FROM tasks WHERE info_hash = ?', (info_hash,))
            conn.commit()

class GhostEngineApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        self.theme_cls.accent_palette = "Teal"
        self.active_tasks = {}
        self.current_viewing_id = None
        self.dialog = None
        
        self.data_dir = getattr(self, 'user_data_dir', '.')
        self.db = Database(os.path.join(self.data_dir, 'seeder.db'))
        self.mem_file = os.path.join(self.data_dir, 'ghost_memory.json')

        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
            try:
                from jnius import autoclass, cast
                Environment = autoclass('android.os.Environment')
                if not Environment.isExternalStorageManager():
                    Intent = autoclass('android.content.Intent')
                    Settings = autoclass('android.provider.Settings')
                    Uri = autoclass('android.net.Uri')
                    PythonActivity = autoclass('org.kivy.android.PythonActivity')
                    activity = cast('android.app.Activity', PythonActivity.mActivity)
                    intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
                    intent.setData(Uri.parse("package:" + activity.getPackageName()))
                    activity.startActivity(intent)
            except: pass

        self.sm = Builder.load_string(KV)
        self.restore_tasks()
        return self.sm

    def on_start(self): Clock.schedule_interval(self.live_ui_ticker, 1.0)

    def format_size(self, mb_value):
        if mb_value >= 1024: return f"{mb_value / 1024:.2f} GB"
        return f"{mb_value:.2f} MB"

    def format_time(self, seconds):
        if seconds < 60: return f"{seconds}s"
        m, s = divmod(seconds, 60)
        if m >= 60:
            h, m = divmod(m, 60)
            return f"{h}h {m}m {s}s"
        return f"{m}m {s}s"

    def load_memory(self):
        if os.path.exists(self.mem_file):
            try:
                with open(self.mem_file, 'r') as f: return json.load(f)
            except: return {}
        return {}

    def save_memory(self, data):
        try:
            with open(self.mem_file, 'w') as f: json.dump(data, f)
        except: pass

    def restore_tasks(self):
        tasks = self.db.get_tasks()
        memory = self.load_memory()
        for t in tasks:
            info_hash, name, peer_id, uploaded_bytes, tracker_url, leechers, key, size_mb, port, ident, s_min, s_max, running = t
            mem_data = memory.get(info_hash, {})
            uploaded_bytes = mem_data.get('uploaded_bytes', uploaded_bytes)
            
            ua = "qBittorrent/4.6.4"
            for fam in CLIENT_MASKS.values():
                for ver, d in fam.items():
                    if d['prefix'] in peer_id: ua = d['ua']

            self.active_tasks[info_hash] = {
                'id': info_hash, 'name': name, 'client_name': ident, 'tracker_url': tracker_url,
                'info_hash': info_hash, 'peer_id': peer_id, 'key': key, 'port': port,
                'ua': ua, 'running': bool(running), 'uploaded_bytes': uploaded_bytes, 'size_mb': size_mb,
                'speed_min': s_min, 'speed_max': s_max, 'current_speed_kb': 0, 
                'seeders': 0, 'peers': leechers, 'next_ping': 10, 'list_item': None,
                'status': "⏳ Initializing", 'announce_status': "⏳ Pending"
            }
            self.spawn_list_item(info_hash)
            if running: threading.Thread(target=self.tracker_loop, args=(info_hash,), daemon=True).start()

    def show_alert(self, title, text):
        if not self.dialog: self.dialog = MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", theme_text_color="Custom", text_color=self.theme_cls.primary_color, on_release=lambda x: self.dialog.dismiss())])
        else: self.dialog.title = title; self.dialog.text = text
        self.dialog.open()

    def open_details(self, task_id):
        self.current_viewing_id = task_id
        task = self.active_tasks[task_id]
        ds = self.sm.get_screen('detail').ids
        ds.detail_name.text = task['name']
        ds.detail_identity.text = f"|- Identity -> {task['client_name']}"
        ds.btn_start.text = "Pause" if task['running'] else "Start"
        self.sm.transition.direction = 'left'
        self.sm.current = 'detail'
        self.update_ui_card(task_id)

    def go_back(self):
        self.current_viewing_id = None
        self.sm.transition.direction = 'right'
        self.sm.current = 'main'

    def add_torrent_dialog(self):
        self.current_path = '/storage/emulated/0/Download' if os.path.exists('/storage/emulated/0/Download') else '/storage/emulated/0'
        box = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        self.path_label = Label(text=self.current_path, size_hint_y=None, height="30dp", color=(0, 1, 0.8, 1), halign="left")
        self.path_label.bind(size=self.path_label.setter('text_size'))
        box.add_widget(self.path_label)
        
        self.rv = Builder.load_string('''
RecycleView:
    viewclass: 'FileButton'
    RecycleBoxLayout:
        default_size: None, dp(55)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'
        spacing: dp(4)
''')
        self.update_rv_data()
        box.add_widget(self.rv)
        
        btn_cancel = Button(text="CANCEL", size_hint_y=None, height="50dp", background_color=(0.8, 0.1, 0.1, 1), bold=True)
        box.add_widget(btn_cancel)
        
        self.file_popup = Popup(title="[ SELECT PAYLOAD ]", title_color=(0, 1, 0.5, 1), content=box, size_hint=(0.95, 0.95), background_color=(0.05, 0.05, 0.05, 1))
        btn_cancel.bind(on_release=self.file_popup.dismiss)
        self.file_popup.open()

    def update_rv_data(self):
        self.path_label.text = f"[ {self.current_path} ]"
        data = []
        if self.current_path != '/storage/emulated/0':
            data.append({'text': '[color=00FFCC][b][ BACK ][/b][/color]  ..', 'is_dir': True, 'filename': '..'})
        try:
            items = os.listdir(self.current_path)
            dirs, files = [], []
            for item in items:
                if item.startswith('.'): continue
                full_path = os.path.join(self.current_path, item)
                if os.path.isdir(full_path): dirs.append(item)
                elif item.lower().endswith('.torrent'): files.append(item)
            dirs.sort(key=str.lower); files.sort(key=str.lower)
            for d in dirs: data.append({'text': f'[color=FFDD00][b][ DIR ][/b][/color]   {d}', 'is_dir': True, 'filename': d})
            for f in files: data.append({'text': f'  {f}', 'is_dir': False, 'filename': f})
        except Exception:
            data.append({'text': f'[color=FF0000]❌ Error reading folder[/color]', 'is_dir': False, 'filename': ''})
        self.rv.data = data

    def on_file_click(self, filename, is_dir):
        if not filename: return
        if is_dir:
            if filename == '..': self.current_path = os.path.dirname(self.current_path)
            else: self.current_path = os.path.join(self.current_path, filename)
            self.update_rv_data()
        else:
            self.file_popup.dismiss()
            self.payload_data = os.path.join(self.current_path, filename)
            self.client_popup = Popup(title_align='center', size_hint=(0.9, 0.6), background_color=(0.1, 0.1, 0.15, 1))
            self.show_main_menu()
            self.client_popup.open()

    def show_main_menu(self, *args):
        self.client_popup.title = "Select client identity:"
        layout = BoxLayout(orientation='vertical', spacing=10, padding=15)
        for family, icon in [("qBittorrent", "🔵"), ("Transmission", "🔴"), ("Deluge", "💧")]:
            btn = Button(text=f"{icon} {family}", background_color=(0.2, 0.2, 0.3, 1), font_size='20sp')
            btn.bind(on_press=lambda x, f=family: self.show_version_menu(f))
            layout.add_widget(btn)
        self.client_popup.content = layout

    def show_version_menu(self, client_family):
        self.client_popup.title = f"Select {client_family} version:"
        layout = BoxLayout(orientation='vertical', spacing=10, padding=15)
        for version_name in CLIENT_MASKS[client_family].keys():
            btn = Button(text=version_name, background_color=(0.25, 0.25, 0.35, 1), font_size='18sp')
            profile = CLIENT_MASKS[client_family][version_name]
            btn.bind(on_press=lambda instance, p=profile, vn=version_name: self.show_speed_menu(p, vn))
            layout.add_widget(btn)
        btn_back = Button(text="⬅ Back", background_color=(0.3, 0.3, 0.3, 1), font_size='18sp')
        btn_back.bind(on_press=self.show_main_menu)
        layout.add_widget(btn_back)
        self.client_popup.content = layout

    def show_speed_menu(self, profile, version_name):
        self.client_popup.title = "⚙️ Select Speed Profile:"
        layout = BoxLayout(orientation='vertical', spacing=10, padding=15)
        btn_slow = Button(text="🐢 Slow (50 - 200 KB/s)", background_color=(0.2, 0.4, 0.2, 1), font_size='18sp')
        btn_slow.bind(on_press=lambda x: self.launch_payload(profile, version_name, 50, 200))
        btn_med = Button(text="🚗 Medium (200 - 500 KB/s)", background_color=(0.4, 0.4, 0.2, 1), font_size='18sp')
        btn_med.bind(on_press=lambda x: self.launch_payload(profile, version_name, 200, 500))
        btn_fast = Button(text="🚀 Fast (500 - 1000 KB/s)", background_color=(0.5, 0.2, 0.2, 1), font_size='18sp')
        btn_fast.bind(on_press=lambda x: self.launch_payload(profile, version_name, 500, 1000))
        btn_back = Button(text="⬅ Back", background_color=(0.3, 0.3, 0.3, 1), font_size='18sp')
        btn_back.bind(on_press=self.show_main_menu)
        for b in [btn_slow, btn_med, btn_fast, btn_back]: layout.add_widget(b)
        self.client_popup.content = layout

    def launch_payload(self, profile, version_name, speed_min, speed_max):
        self.client_popup.dismiss()
        threading.Thread(target=self.init_torrent_task, args=(self.payload_data, profile, version_name, speed_min, speed_max), daemon=True).start()

    def get_val(self, d, key):
        b_key = key.encode('utf-8')
        if b_key in d: return d[b_key]
        if key in d: return d[key]
        return None

    def init_torrent_task(self, file_path, profile, client_name, speed_min, speed_max):
        try:
            with open(file_path, 'rb') as f: raw_data = f.read()
            if b'<html' in raw_data.lower() or b'<!doctype' in raw_data.lower():
                Clock.schedule_once(lambda dt: self.show_alert("Security Block", "HTML Webpage detected. Login to tracker first."))
                return

            data = bencode.bdecode(raw_data)
            info = self.get_val(data, 'info')
            if not info: return
            
            announce_val = self.get_val(data, 'announce')
            announce_list_val = self.get_val(data, 'announce-list')
            announce_url = ""
            if announce_val: announce_url = announce_val.decode('utf-8') if isinstance(announce_val, bytes) else str(announce_val)
            elif announce_list_val:
                first_url = announce_list_val[0][0]
                announce_url = first_url.decode('utf-8') if isinstance(first_url, bytes) else str(first_url)

            info_hash = hashlib.sha1(bencode.bencode(info)).hexdigest()
            name_val = self.get_val(info, 'name')
            name = name_val.decode('utf-8') if isinstance(name_val, bytes) else str(name_val) if name_val else "Unknown"
            
            length_val = self.get_val(info, 'length')
            files = self.get_val(info, 'files')
            if files: size_bytes = sum((self.get_val(f, 'length') or 0) for f in files)
            else: size_bytes = int(length_val) if length_val else 0
            size_mb = size_bytes / (1024*1024)
            
            mem = self.load_memory()
            if info_hash in mem:
                uploaded_bytes = mem[info_hash].get('uploaded_bytes', 0)
                peer_id = mem[info_hash].get('peer_id')
                port = mem[info_hash].get('port')
                key = mem[info_hash].get('key')
            else:
                uploaded_bytes = 0
                peer_id = profile['prefix'] + ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                port = random.randint(50000, 60000)
                key = ''.join(random.choices(string.hexdigits.upper(), k=8))
                mem[info_hash] = {'uploaded_bytes': uploaded_bytes, 'peer_id': peer_id, 'port': port, 'key': key}
                self.save_memory(mem)

            self.db.add_task(info_hash, name, peer_id, announce_url, key, size_mb, port, client_name, speed_min, speed_max)
            
            self.active_tasks[info_hash] = {
                'id': info_hash, 'name': name, 'client_name': client_name, 'tracker_url': announce_url,
                'info_hash': info_hash, 'peer_id': peer_id, 'key': key, 'port': port,
                'ua': profile['ua'], 'running': True, 'uploaded_bytes': uploaded_bytes, 'size_mb': size_mb,
                'speed_min': speed_min, 'speed_max': speed_max, 'current_speed_kb': 0,
                'seeders': 0, 'peers': 0, 'next_ping': 10, 'list_item': None,
                'status': "⏳ Initializing", 'announce_status': "⏳ Pending"
            }
            
            Clock.schedule_once(lambda dt: self.spawn_list_item(info_hash))
            threading.Thread(target=self.tracker_loop, args=(info_hash,), daemon=True).start()
            
        except Exception as e:
            Clock.schedule_once(lambda dt, err=str(e): self.show_alert("Engine Crash", str(err)))

    def spawn_list_item(self, task_id):
        task = self.active_tasks[task_id]
        item = ThreeLineListItem(
            text=f"{task['name'][:35]}...",
            secondary_text=f"Status: {task['status']} | ⬆ 0 KB/s",
            tertiary_text="Up: 0.00 MB / 0.00 MB  |  Ratio: 0.000",
            on_release=lambda x: self.open_details(task_id)
        )
        task['list_item'] = item
        self.sm.get_screen('main').ids.active_tasks_list.add_widget(item)

    def live_ui_ticker(self, dt):
        tz = pytz.timezone('Asia/Kolkata')
        curr_hour = datetime.datetime.now(tz).hour
        is_sleeping = (2 <= curr_hour < 8)

        for task_id, task in self.active_tasks.items():
            if not task['running']:
                task['status'] = "⏸️ Paused"
                self.update_ui_card(task_id)
                continue

            up_mb = task['uploaded_bytes'] / (1024*1024)
            if task['size_mb'] > 0.05 and up_mb >= task['size_mb']:
                task['status'] = "✅ Completed"
                task['current_speed_kb'] = 0.0
                self.update_ui_card(task_id)
                continue

            if task['peers'] == 0:
                task['status'] = "👻 Lurking (0 Leechers)"
                task['current_speed_kb'] = 0.0
            elif is_sleeping:
                task['status'] = "💤 Sleeping (Humanized)"
                task['current_speed_kb'] = 0.0
            else:
                task['status'] = "🚀 Seeding (Ghost)"
                var = random.uniform(-15.0, 15.0)
                base = task['current_speed_kb'] if task['current_speed_kb'] > 0 else task['speed_min']
                new_speed = base + var
                if new_speed < task['speed_min']: new_speed = task['speed_min'] + random.uniform(0, 5)
                if new_speed > task['speed_max']: new_speed = task['speed_max'] - random.uniform(0, 5)
                task['current_speed_kb'] = new_speed
                task['uploaded_bytes'] += int(new_speed * 1024)

            if task['next_ping'] > 0: task['next_ping'] -= 1
            self.update_ui_card(task_id)

    def announce_udp(self, task, event_name=None):
        try:
            parsed = urllib.parse.urlparse(task['tracker_url'])
            host, port = parsed.hostname, parsed.port
            if not port: return False, "No port"
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(10)
            
            transaction_id = random.getrandbits(32)
            packet = struct.pack(">QII", 0x41727101980, 0, transaction_id)
            sock.sendto(packet, (host, port))
            res, _ = sock.recvfrom(16)
            action, res_transaction_id, connection_id = struct.unpack(">IIQ", res)
            if action != 0 or res_transaction_id != transaction_id: return False, "Connect failed"
            
            event = 2 if event_name == 'started' else 3 if event_name == 'stopped' else 1 if event_name == 'completed' else 0
            key_int = int(task['key'], 16)
            transaction_id = random.getrandbits(32)
            packet = struct.pack(">QII", connection_id, 1, transaction_id)
            packet += bytes.fromhex(task['info_hash']) + task['peer_id'].encode('ascii')
            packet += struct.pack(">QQQIIIiH", 0, 0, int(task['uploaded_bytes']), int(event), 0, key_int, -1, int(task['port']))
            
            sock.sendto(packet, (host, port))
            res, _ = sock.recvfrom(20)
            action, res_transaction_id, interval, leechers, seeders = struct.unpack(">IIIII", res[:20])
            
            task['seeders'] = seeders
            task['peers'] = leechers
            return True, "OK"
        except Exception as e: return False, f"UDP Err: {e}"

    def announce_http(self, task, event_name=None):
        try:
            hash_bytes = bytes.fromhex(task['info_hash'])
            encoded_hash = urllib.parse.quote(hash_bytes)
            headers = {'User-Agent': task['ua'], 'Accept-Encoding': 'gzip', 'Connection': 'close'}
            params = {
                'peer_id': task['peer_id'], 'port': task['port'], 'uploaded': int(task['uploaded_bytes']),
                'downloaded': 0, 'left': 0, 'corrupt': 0, 'key': task['key'], 'compact': 1
            }
            if event_name: params['event'] = event_name
            url = f"{task['tracker_url']}{'&' if '?' in task['tracker_url'] else '?'}{urllib.parse.urlencode(params)}&info_hash={encoded_hash}"
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                try:
                    dec = bencode.bdecode(res.content)
                    if b'failure reason' in dec: return False, dec[b'failure reason'].decode('utf-8')
                    task['peers'] = dec.get(b'incomplete', dec.get('incomplete', 0))
                    task['seeders'] = dec.get(b'complete', dec.get('complete', 0))
                except: pass
                return True, "OK"
            return False, f"HTTP {res.status_code}"
        except Exception as e: return False, str(e)

    def tracker_loop(self, task_id):
        task = self.active_tasks[task_id]
        is_udp = task['tracker_url'].startswith("udp://")
        
        success, msg = self.announce_udp(task, 'started') if is_udp else self.announce_http(task, 'started')
        task['announce_status'] = "✅ Announce OK" if success else f"❌ {msg}"
        
        interval = 1800 if success else 60
        task['next_ping'] = interval

        while task_id in self.active_tasks and task['running']:
            for _ in range(interval):
                if task_id not in self.active_tasks or not task['running']: break
                if task['status'] == "✅ Completed": break
                time.sleep(1)
            
            if task_id not in self.active_tasks or not task['running']: break
            
            if task['status'] == "✅ Completed":
                success, msg = self.announce_udp(task, 'completed') if is_udp else self.announce_http(task, 'completed')
                task['announce_status'] = "✅ Announce OK" if success else f"❌ {msg}"
                task['running'] = False
                break
                
            success, msg = self.announce_udp(task) if is_udp else self.announce_http(task)
            task['announce_status'] = "✅ Announce OK" if success else f"❌ {msg}"
            
            interval = 1800 if success else 60
            task['next_ping'] = interval
            
            self.db.update_stats(task_id, task['uploaded_bytes'], task['peers'])
            mem = self.load_memory()
            if task_id in mem:
                mem[task_id]['uploaded_bytes'] = task['uploaded_bytes']
                self.save_memory(mem)

    def update_ui_card(self, task_id):
        if task_id not in self.active_tasks: return
        task = self.active_tasks[task_id]
        
        up_mb = task['uploaded_bytes'] / (1024*1024)
        ratio = (up_mb / task['size_mb']) if task['size_mb'] > 0 else 0.0
        percent = min(100.0, ratio * 100)
        
        up_str = self.format_size(up_mb)
        tot_str = self.format_size(task['size_mb'])
        time_str = self.format_time(task['next_ping'])

        if task['list_item']:
            task['list_item'].secondary_text = f"{task['status']} | ⬆ {int(task['current_speed_kb'])} KB/s"
            task['list_item'].tertiary_text = f"Up: {up_str} / {tot_str}  |  Ratio: {ratio:.3f}"
            
        if self.current_viewing_id == task_id:
            ds = self.sm.get_screen('detail').ids
            ds.progress_bar.value = percent
            ds.progress_text.text = f"]  {percent:.1f}%"
            
            ds.detail_uploaded.text = f"|- Uploaded -> {up_str} / {tot_str} | Ratio -> {ratio:.3f}"
            ds.speed_label.text = f"|- Speed -> {int(task['current_speed_kb'])} KB/s"
            ds.status_label.text = f"|- Status -> {task['status']}"
            ds.detail_announce.text = f"|- Announce -> {task.get('announce_status', '⏳ Pending')} | Next -> {time_str}"
            ds.detail_peers.text = f"\\- Seeders -> {task['seeders']} | Leechers -> {task['peers']}"

    def toggle_seed(self):
        if not self.current_viewing_id: return
        task = self.active_tasks[self.current_viewing_id]
        task['running'] = not task['running']
        self.db.update_running(self.current_viewing_id, 1 if task['running'] else 0)
        self.sm.get_screen('detail').ids.btn_start.text = "Pause" if task['running'] else "Start"
        if task['running']: threading.Thread(target=self.tracker_loop, args=(self.current_viewing_id,), daemon=True).start()
        else:
            if task['tracker_url'].startswith("udp://"): self.announce_udp(task, 'stopped')
            else: self.announce_http(task, 'stopped')
        self.update_ui_card(self.current_viewing_id)

    def delete_current_task(self):
        if not self.current_viewing_id: return
        task_id = self.current_viewing_id
        task = self.active_tasks[task_id]
        task['running'] = False
        if task['tracker_url'].startswith("udp://"): self.announce_udp(task, 'stopped')
        else: self.announce_http(task, 'stopped')
        self.db.remove_task(task_id)
        mem = self.load_memory()
        if task_id in mem:
            del mem[task_id]
            self.save_memory(mem)
        self.sm.get_screen('main').ids.active_tasks_list.remove_widget(task['list_item'])
        del self.active_tasks[task_id]
        self.go_back()

if __name__ == '__main__':
    GhostEngineApp().run()

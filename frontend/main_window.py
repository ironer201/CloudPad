"""Main window: wires Front-end + Back-end + Cloud together."""
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import config
from backend.auth import AuthState
from backend.file_manager import FileManager
from backend.settings import Settings
from cloud.supabase_api import SupabaseClient
from cloud.sync_manager import SyncManager
from frontend.auth_dialog import AuthDialog
from frontend.editor_panel import EditorPanel
from frontend.sidebar import Sidebar


class MainWindow:
    def __init__(self, root):
        self.root = root
        root.title("CloudPad")
        root.geometry("1000x620")
        root.minsize(680, 420)

        # back-end + cloud
        self.settings = Settings()
        self.auth = AuthState()
        self.client = SupabaseClient(config.SUPABASE_URL,
                                     config.SUPABASE_ANON_KEY)
        self.sync = SyncManager()

        # state
        self.current_file = None      # local path (or None)
        self.current_cloud_id = None  # cloud doc id (or None)
        self.cloud_docs = []
        self.auth_dialog = None
        self._last_call = None
        self._tried_refresh = False

        self._build_menu()
        self._build_layout()
        self.sync.poll(root, self._on_cloud_result)

    # ============================================================ UI ====
    def _build_menu(self):
        menubar = tk.Menu(self.root)
        m_file = tk.Menu(menubar, tearoff=0)
        m_file.add_command(label="New", accelerator="Ctrl+N", command=self.new_file)
        m_file.add_command(label="Open…", accelerator="Ctrl+O", command=self.open_file)
        m_file.add_command(label="Save", accelerator="Ctrl+S", command=self.save_file)
        m_file.add_command(label="Save As…", command=self.save_file_as)
        m_file.add_separator()
        m_file.add_command(label="Exit", command=self.root.destroy)
        menubar.add_cascade(label="File", menu=m_file)

        m_cloud = tk.Menu(menubar, tearoff=0)
        m_cloud.add_command(label="Save to Cloud", accelerator="Ctrl+Shift+S",
                            command=self.cloud_save)
        m_cloud.add_command(label="Refresh cloud list", command=self.cloud_list)
        m_cloud.add_command(label="Delete cloud copy…", command=self.cloud_delete)
        menubar.add_cascade(label="Cloud", menu=m_cloud)

        self.root.config(menu=menubar)
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-N>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-O>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-S>", lambda e: self.cloud_save())

    def _build_layout(self):
        """Left panel (titles) | right panel (editor) — right is 3x bigger."""
        pane = ttk.PanedWindow(self.root, orient="horizontal")
        pane.pack(fill="both", expand=True)
        self.sidebar = Sidebar(pane, self)
        self.editor = EditorPanel(pane, self)
        pane.add(self.sidebar.frame, weight=1)
        pane.add(self.editor.frame, weight=3)

    # ==================================================== local files ===
    def new_file(self):
        if not self._confirm_discard():
            return
        self.editor.set_text("")
        self.editor.set_title("Untitled")
        self.current_file = self.current_cloud_id = None
        self.update_window_title()

    def open_file(self, path=None):
        if not self._confirm_discard():
            return

        if path is None:
            path = self._ask_open_path()

        if not path:
            return

        try:
            content, _ = FileManager.read(path)
        except (OSError, ValueError) as e:
            messagebox.showerror(
                "CloudPad — Cannot Open File",
                f"Could not open:\n{os.path.basename(path)}\n\n{e}",
                parent=self.root,
            )
            return

        self.editor.set_text(content)
        self.editor.set_title(os.path.basename(path))
        self.current_file, self.current_cloud_id = path, None
        self.settings.add_recent(path)
        # self.editor.refresh_recent()
        self.sidebar.refresh_local()
        self.update_window_title()

    def _ask_open_path(self):
        """Prefer zenity on Linux, fall back to tkinter filedialog."""
        import sys

        if sys.platform.startswith("linux"):
            try:
                import subprocess
                result = subprocess.run(
                    ["zenity", "--file-selection",
                     "--title=Open File",
                     "--filename=" + os.path.expanduser("~") + "/",
                     "--file-filter=Text & Markdown | *.txt *.md *.log *.ini *.cfg *.conf",
                     "--file-filter=Source Code | *.py *.js *.ts *.html *.css *.json *.xml *.yaml *.yml *.sh *.c *.cpp *.h *.java",
                     "--file-filter=All Files | *"],
                    capture_output=True, text=True,
                )

                if result.returncode == 0:
                    return result.stdout.strip() if result.stdout.strip() else None
                elif result.returncode == 1:
                    return None
            except FileNotFoundError:
                pass
            except Exception:
                pass

        return filedialog.askopenfilename(parent=self.root)

    def _write_local(self, path):
        """Write editor content to path. Returns True on success."""
        try:
            FileManager.write(path, self.editor.get_text())
        except OSError as e:
            messagebox.showerror(
                "CloudPad — Cannot Save File",
                f"Could not save:\n{os.path.basename(path)}\n\n{e}",
                parent=self.root,
            )
            return False
        self.editor.text.edit_modified(False)
        self.editor.set_status(f"Saved {os.path.basename(path)}")
        self.update_window_title()
        return True

    def save_file(self):
        if self.current_file:
            if self._write_local(self.current_file):
                self.settings.add_recent(self.current_file)
                # self.editor.refresh_recent()
                self.sidebar.refresh_local()
        else:
            self.save_file_as()

    def save_file_as(self):
        import sys, subprocess
        path = ""
        if sys.platform.startswith("linux"):
            try:
                path = subprocess.check_output(
                    ["zenity", "--file-selection", "--save",
                     "--confirm-overwrite",
                     "--file-filter=Text files | *.txt",
                     "--file-filter=All files | *"],
                    text=True
                ).strip()
            except (subprocess.CalledProcessError, FileNotFoundError):
                path = ""
            if not path:
                return
        else:
            path = filedialog.asksaveasfilename(
                parent=self.root,
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
            if not path:
                return
        if not self._write_local(path):
            return
        self.current_file = path
        self.settings.add_recent(path)
        # self.editor.refresh_recent()
        self.sidebar.refresh_local()
        self.update_window_title()

    # ========================================================= cloud ====
    def show_login(self, after_login=None):
        if not config.CLOUD_CONFIGURED:
            messagebox.showwarning(
                "CloudPad",
                "Cloud is not configured yet.\n\n"
                "Open the .env file next to the app and fill in\n"
                "SUPABASE_URL and SUPABASE_ANON_KEY,\n"
                "then restart CloudPad.")
            return
        if self.auth.logged_in:
            if after_login:
                after_login()
            return
        if self.auth_dialog is None:
            self.auth_dialog = AuthDialog(self.root, self, after_login)
        else:
            self.auth_dialog.top.focus_force()
    def cloud_save(self):
        if not self.auth.logged_in:
            self.show_login(after_login=self._push_to_cloud)
        else:
            self._push_to_cloud()

    def _push_to_cloud(self):
        if not self.auth.logged_in:
            return
        title = self.editor.get_title() or "Untitled"
        content = self.editor.get_text()
        self.editor.set_status("Uploading to cloud…")
        if self.current_cloud_id:
            self._cloud("upload", self.client.update_document,
                        self.auth.access_token, self.current_cloud_id,
                        title, content)
        else:
            self._cloud("upload", self.client.upload_document,
                        self.auth.access_token, self.auth.user_id,
                        title, content)

    def cloud_list(self):
        if self.auth.logged_in:
            self.editor.set_status("Loading cloud documents…")
            self._cloud("list", self.client.list_documents,
                        self.auth.access_token)

    def open_cloud_doc(self, index):
        if not self._confirm_discard():
            return
        doc = self.cloud_docs[index]
        self.editor.set_status("Downloading…")
        self._cloud("download", self.client.download_document,
                    self.auth.access_token, doc["id"])

    def cloud_delete(self):
        if not self.auth.logged_in or not self.current_cloud_id:
            messagebox.showinfo("CloudPad", "This document has no cloud copy.")
            return
        if messagebox.askyesno("CloudPad",
                               "Delete the cloud copy of this document?"):
            self._cloud("delete", self.client.delete_document,
                        self.auth.access_token, self.current_cloud_id)

    def sign_out(self):
        if self.auth.logged_in:
            self.sync.submit("logout", self.client.sign_out,
                             self.auth.access_token)
        self.auth.clear()
        self.cloud_docs = []
        self.current_cloud_id = None
        self._last_call = None
        self._tried_refresh = False
        self.sidebar.set_user(None)
        self.sidebar.refresh_cloud([])
        self.editor.set_status("Signed out (cloud features disabled)")

    def _cloud(self, op, func, *args):
        """Remember the call so it can be auto-retried after token refresh."""
        self._last_call = (op, func, args)
        self.sync.submit(op, func, *args)

    # ============================================ cloud results (UI thread)
    def _on_cloud_result(self, op, status, result):
        # ---- login / signup (handled by the dialog) -------------------
        if op in ("signin", "signup") and self.auth_dialog:
            if status != "ok":
                self.auth_dialog.fail(result)
            elif op == "signin":
                after = self.auth_dialog.after_login
                self.auth_dialog.close()
                self._finish_login(result, after)
            else:  # signup ok -> sign in automatically
                self.auth_dialog.notify("Account created — signing in…")
                self.sync.submit("signin", self.client.sign_in,
                                 self.auth_dialog.last_email,
                                 self.auth_dialog.last_password)
            return

        # ---- errors ----------------------------------------------------
        if status != "ok":
            if op == "refresh":
                self.sign_out()
                self.editor.set_status("Session expired — please sign in again")
                return
            if (self._is_auth_error(result) and self.auth.refresh_token
                    and not self._tried_refresh):
                self._tried_refresh = True
                self.editor.set_status("Session expired — refreshing…")
                self.sync.submit("refresh", self.client.refresh,
                                 self.auth.refresh_token)
                return
            self.editor.set_status("Cloud error")
            self._last_call = None
            self._tried_refresh = False
            messagebox.showerror("CloudPad", result)
            return

        # ---- success ---------------------------------------------------
        if op == "refresh":
            self.auth.set_session(result)
            self._tried_refresh = False
            if self._last_call:
                c_op, func, args = self._last_call
                # Rebuild args with the fresh access token; stored args
                # still hold the expired token from before the refresh.
                fresh_args = (self.auth.access_token,) + tuple(args[1:]) if args else ()
                self._last_call = (c_op, func, fresh_args)
                self.sync.submit(c_op, func, *fresh_args)   # silent retry
            else:
                self.editor.set_status("Session refreshed")
        elif op == "upload":
            if result:                       # insert returns the new id
                self.current_cloud_id = result
            self._last_call = None
            self._tried_refresh = False
            self.editor.text.edit_modified(False)
            self.editor.set_status("Saved to cloud \u2713")
            self.cloud_list()
        elif op == "list":
            self.cloud_docs = result or []
            self._last_call = None
            self._tried_refresh = False
            self.sidebar.refresh_cloud(self.cloud_docs)
        elif op == "download":
            self.editor.set_text(result.get("content", ""))
            self.editor.set_title(result.get("title", "Untitled"))
            self.current_file = None
            self.current_cloud_id = result.get("id")
            self._last_call = None
            self._tried_refresh = False
            self.update_window_title()
            self.editor.set_status("Downloaded from cloud \u2713")
        elif op == "delete":
            self.current_cloud_id = None
            self._last_call = None
            self._tried_refresh = False
            self.editor.set_status("Cloud copy deleted")
            self.cloud_list()

    def _finish_login(self, session, after=None):
        self.auth.set_session(session)
        self._tried_refresh = False
        self.sidebar.set_user(self.auth.user_email)
        self.editor.set_status("Signed in as %s" % self.auth.user_email)
        self.cloud_list()
        if after:                      # continue what the user wanted to do
            after()

    # =========================================================== misc ===
    @staticmethod
    def _is_auth_error(msg):
        m = str(msg).lower()
        return "401" in m or "jwt" in m or "invalid api key" in m

    def _confirm_discard(self):
        if not self.editor.is_modified():
            return True
        return messagebox.askyesno("CloudPad", "Discard unsaved changes?")

    def update_window_title(self):
        name = self.editor.get_title() or "Untitled"
        star = " *" if self.editor.is_modified() else ""
        self.root.title("%s%s — CloudPad" % (name, star))

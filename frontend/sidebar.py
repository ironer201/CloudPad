"""LEFT panel: app title, recent file titles, cloud document titles, account."""
import os
import tkinter as tk

from frontend import theme as T


class Sidebar:
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, width=230, bg=T.BG)
        self.frame.pack_propagate(False)

        tk.Label(self.frame, text="CloudPad", bg=T.BG, fg=T.ACCENT,
                 font=(T.UI_FONT, 14, "bold")).pack(pady=(14, 0))
        tk.Label(self.frame, text="offline-first notepad", bg=T.BG, fg=T.MUTED,
                 font=(T.UI_FONT, 8)).pack()

        # ---- account (only needed for cloud) --------------------------
        acct = tk.Frame(self.frame, bg=T.BG)
        acct.pack(fill="x", padx=12, pady=10)
        self.user_lbl = tk.Label(acct, text="Not signed in", bg=T.BG,
                                 fg=T.MUTED, anchor="w")
        self.user_lbl.pack(side="left", fill="x", expand=True)
        self.auth_btn = tk.Button(acct, text="Login", width=7, bd=0,
                                  bg=T.ACCENT, fg="white", relief="flat",
                                  command=self._auth_click)
        self.auth_btn.pack(side="right")

# ---- recent local file titles ---------------------------------
        tk.Label(self.frame, text="RECENT FILES", bg=T.BG, fg=T.MUTED,
                anchor="w", font=(T.UI_FONT, 8, "bold")
                ).pack(fill="x", padx=12)

        # container + scrollbar for recent files
        recent_wrap = tk.Frame(self.frame, bg=T.PANEL)
        recent_wrap.pack(fill="both", expand=True, padx=12, pady=(2, 8))

        self.recent_canvas = tk.Canvas(recent_wrap, bg=T.PANEL,
                                    highlightthickness=0, bd=0)
        self.recent_canvas.pack(side="left", fill="both", expand=True)

        recent_sb = tk.Scrollbar(recent_wrap, orient="vertical",
                                command=self.recent_canvas.yview)
        recent_sb.pack(side="right", fill="y")
        self.recent_canvas.configure(yscrollcommand=recent_sb.set)

        self.recent_inner = tk.Frame(self.recent_canvas, bg=T.PANEL)
        self.recent_window = self.recent_canvas.create_window(
            (0, 0), window=self.recent_inner, anchor="nw")

        self.recent_inner.bind(
            "<Configure>",
            lambda e: self.recent_canvas.configure(
                scrollregion=self.recent_canvas.bbox("all")))
        self.recent_canvas.bind(
            "<Configure>",
            lambda e: self.recent_canvas.itemconfig(
                self.recent_window, width=e.width))
        # ---- cloud document titles ------------------------------------
        tk.Label(self.frame, text="CLOUD DOCUMENTS", bg=T.BG, fg=T.MUTED,
                 anchor="w", font=(T.UI_FONT, 8, "bold")
                 ).pack(fill="x", padx=12)
        self.cloud_list = tk.Listbox(
            self.frame, bg=T.PANEL, fg=T.FG, relief="flat", bd=0,
            highlightthickness=0, selectbackground=T.ACCENT, activestyle="none")
        self.cloud_list.pack(fill="both", expand=True, padx=12, pady=(2, 12))
        self.cloud_list.bind("<Double-1>", self._open_cloud)
        self.cloud_list.bind("<Return>", self._open_cloud)

        self.refresh_local()
        self.refresh_cloud([])

    # ------------------------------------------------------------ refresh
    def refresh_local(self):
        for w in self.recent_inner.winfo_children():
            w.destroy()

        for path in self.app.settings.recent_files:
            self._add_recent_row(path)
    def _add_recent_row(self, path):
        row = tk.Frame(self.recent_inner, bg=T.PANEL)
        row.pack(fill="x", pady=1)

        name = os.path.basename(path)
        lbl = tk.Label(row, text="  " + name, bg=T.PANEL, fg=T.FG,
                    anchor="w", cursor="hand2")
        lbl.pack(side="left", fill="x", expand=True)

        # open on click
        lbl.bind("<Button-1>", lambda e, p=path: self.app.open_file(p))

        x = tk.Label(row, text="✕", bg=T.PANEL, fg=T.MUTED,
                    cursor="hand2", padx=6)
        x.pack(side="right")
        x.bind("<Button-1>", lambda e, p=path: self._remove_recent(p))
        x.bind("<Enter>", lambda e, w=x: w.config(fg=T.ACCENT))
        x.bind("<Leave>", lambda e, w=x: w.config(fg=T.MUTED))

    def _remove_recent(self, path):
        self.app.settings.remove_recent_file(path)
        self.refresh_local()
    def refresh_cloud(self, docs):
        self.cloud_list.delete(0, "end")
        if not docs:
            hint = ("  (sign in for cloud docs)"
                    if not self.app.auth.logged_in else "  (no documents yet)")
            self.cloud_list.insert("end", hint)
            return
        for d in docs:
            self.cloud_list.insert("end", "  " + d.get("title", "Untitled"))

    def set_user(self, email):
        if email:
            self.user_lbl.config(text=email, fg=T.FG)
            self.auth_btn.config(text="Logout")
        else:
            self.user_lbl.config(text="Not signed in", fg=T.MUTED)
            self.auth_btn.config(text="Login")

    # ------------------------------------------------------------- events
    def _auth_click(self):
        if self.app.auth.logged_in:
            self.app.sign_out()
        else:
            self.app.show_login()

    def _open_local(self, _event):
        sel = self.local_list.curselection()
        if sel:
            self.app.open_file(self.app.settings.recent_files[sel[0]])

    def _open_cloud(self, _event):
        if not self.app.auth.logged_in or not self.app.cloud_docs:
            return
        sel = self.cloud_list.curselection()
        if sel:
            self.app.open_cloud_doc(sel[0])
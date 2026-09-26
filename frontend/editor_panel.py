"""RIGHT panel (the big one): toolbar, document title, the text editor,
status line and a recent-files quick strip at the bottom."""
import os
import tkinter as tk
from tkinter import ttk

from frontend import theme as T


class EditorPanel:
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, bg=T.SURFACE)
        self._count_job = None
        # default editor font size
        self._font_size = 11          
        self._min_font = 6
        self._max_font = 40

        # ---- toolbar --------------------------------------------------
        bar = tk.Frame(self.frame, bg=T.SURFACE)
        bar.pack(fill="x", padx=10, pady=(8, 4))
        for text, cmd in (("New", app.new_file), ("Open", app.open_file),
                          ("Save", app.save_file)):
            tk.Button(bar, text=text, command=cmd, relief="flat", bd=0,
                      bg=T.PANEL, fg=T.FG, width=7,
                      activebackground=T.ACCENT).pack(side="left", padx=(0, 6),pady=(0, 10))
        tk.Button(bar, text="\u2601 Save to Cloud", relief="flat", bd=0,
                  bg=T.ACCENT, fg="white", width=15,
                  command=app.cloud_save).pack(side="left", padx=6,pady=(0, 10))

        # ---- document title -------------------------------------------
        row = tk.Frame(self.frame, bg=T.SURFACE)
        row.pack(fill="x", padx=10)
        tk.Label(row, text="Title", bg=T.SURFACE, fg=T.MUTED,
                font=(T.UI_FONT, 14)).pack(side="left", padx=(0, 9))

        self.title_var = tk.StringVar(value="Untitled")

        self.title_entry = tk.Entry(row, textvariable=self.title_var, bg=T.PANEL, fg=T.FG,
                                    relief="flat", font=(T.UI_FONT, 14))
        self.title_entry.pack(side="left", fill="x", expand=True,pady=(0, 7))

        # ---- placeholder behavior ----
        self._title_is_placeholder = True



        def _title_focus_in(event):
            if self._title_is_placeholder:
                self.title_var.set("")
                self._title_is_placeholder = False

        def _title_focus_out(event):
            if self.title_var.get().strip() == "":
                self.title_var.set("Untitled")
                self._title_is_placeholder = True

        def _title_delete_prev_word(event):
            entry = event.widget
            pos = entry.index("insert")
            text = entry.get()
            i = pos
            while i > 0 and text[i - 1].isspace():
                i -= 1
            while i > 0 and not text[i - 1].isspace():
                i -= 1
            entry.delete(i, pos)
            return "break"

        def _title_select_all(event):
            event.widget.select_range(0, "end")
            event.widget.icursor("end")
            return "break"

        self.title_entry.bind("<FocusIn>", _title_focus_in)
        self.title_entry.bind("<FocusOut>", _title_focus_out)
        self.title_entry.bind("<Control-BackSpace>", _title_delete_prev_word)
        self.title_entry.bind("<Control-a>", _title_select_all)
        self.title_entry.bind("<Control-A>", _title_select_all)

        # ---- bottom bar (pack BEFORE the editor so it keeps its space) -
        bottom = tk.Frame(self.frame, bg=T.BG)
        bottom.pack(fill="x", side="bottom")
        self.status_lbl = tk.Label(bottom, text="Ready", bg=T.BG, fg=T.MUTED,
                                   anchor="w", font=(T.UI_FONT, 8))
        self.status_lbl.pack(side="left", fill="x", expand=True, padx=10)
        self.counts_lbl = tk.Label(bottom, text="", bg=T.BG, fg=T.MUTED,
                                   font=(T.UI_FONT, 8))
        self.counts_lbl.pack(side="left")
        self.recent_bar = tk.Frame(bottom, bg=T.BG)
        self.recent_bar.pack(side="left", padx=6)

        # ---- the editor itself ----------------------------------------
        body = tk.Frame(self.frame, bg=T.SURFACE)
        body.pack(fill="both", expand=True, padx=10, pady=8)
        self.text = tk.Text(body, wrap="word", undo=True, bg=T.PANEL, fg=T.FG,
                            insertbackground=T.FG, relief="flat", bd=0,
                            padx=8, pady=6, font=(T.MONO_FONT, self._font_size),
                            selectbackground=T.ACCENT)
        scroll = ttk.Scrollbar(body, command=self.text.yview)
        self.text.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)
        # Fix in here for shortcut
        self.text.bind("<<Modified>>", lambda e: self.app.update_window_title())
        self.text.bind("<KeyRelease>", lambda e: self._schedule_counts())
        self.text.bind("<Control-BackSpace>", self._text_delete_prev_word)
        self.text.bind("<Control-Key-a>", self._text_select_all)
        self.text.bind("<Control-Key-A>", self._text_select_all)
                # ---- zoom (editor only) ---------------------------------------
        self.text.bind("<Control-MouseWheel>", self._on_ctrl_wheel)
        self.text.bind("<Control-Button-4>", self._on_ctrl_wheel)
        self.text.bind("<Control-Button-5>", self._on_ctrl_wheel)
        self.text.bind("<Control-minus>", self._zoom_out)
        self.text.bind("<Control-KP_Subtract>", self._zoom_out)
        self.text.bind("<Control-equal>", self._zoom_in)
        self.text.bind("<Control-plus>", self._zoom_in)
        self.text.bind("<Control-KP_Add>", self._zoom_in)
        self.text.bind("<Control-Key-0>", self._zoom_reset)
                # ---- zoom (editor only) ---------------------------------------
        self.text.bind("<Control-MouseWheel>", self._on_ctrl_wheel)     # Win/macOS
        self.text.bind("<Control-Button-4>", self._on_ctrl_wheel)       # Linux scroll up
        self.text.bind("<Control-Button-5>", self._on_ctrl_wheel)       # Linux scroll down
        self.text.bind("<Control-minus>", self._zoom_out)
        self.text.bind("<Control-KP_Subtract>", self._zoom_out)
        self.text.bind("<Control-equal>", self._zoom_in)                # Ctrl + = (no shift)
        self.text.bind("<Control-plus>", self._zoom_in)                 # Ctrl + Shift + =
        self.text.bind("<Control-KP_Add>", self._zoom_in)
        self.text.bind("<Control-Key-0>", self._zoom_reset)             # Ctrl+0 = reset

        # self.refresh_recent()
        self._update_counts()

    # ---------------------------------------------------------- accessors
    def get_text(self):
        return self.text.get("1.0", "end-1c")

    def set_text(self, content):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.text.edit_modified(False)
        self._update_counts()

    def get_title(self):
        return self.title_var.get().strip()

    def set_title(self, title):
        text = (title or "").strip() or "Untitled"
        self.title_var.set(text)
        # Keep placeholder flag in sync, otherwise focusing the entry
        # would wipe a real filename thinking it is still the placeholder.
        self._title_is_placeholder = (text == "Untitled")

    def set_status(self, msg):
        self.status_lbl.config(text=msg)

    def is_modified(self):
        return bool(self.text.edit_modified())

    # def refresh_recent(self):
    #     """Rebuild the quick recent-files strip in the bottom bar."""
    #     for child in self.recent_bar.winfo_children():
    #         child.destroy()
    #     try:
    #         files = self.app.settings.recent_files[:3]
    #     except Exception:
    #         files = []
    #     for path in files:
    #         name = os.path.basename(path)
    #         tk.Button(self.recent_bar, text=name, relief="flat", bd=0,
    #                   bg=T.PANEL, fg=T.MUTED, font=(T.UI_FONT, 8),
    #                   command=lambda p=path: self.app.open_file(p)).pack(side="left", padx=2)

    # ------------------------------------------------------------ helpers
    def _schedule_counts(self):
        """Throttled: recount at most ~3x/sec — no lag while typing fast."""
        if self._count_job is None:
            self._count_job = self.text.after(300, self._update_counts)

    def _update_counts(self):
        self._count_job = None
        n = self.text.count("1.0", "end-1c", "chars")  # counted inside Tk = cheap
        if isinstance(n, tuple):
            n = n[0]
        self.counts_lbl.config(text="%d chars" % (n or 0))

    #This is for the text shortcut key for Ctrl + A and Ctrl + Backspace
    def _text_select_all(self, event):
        event.widget.tag_add("sel", "1.0", "end-1c")
        event.widget.mark_set("insert", "1.0")
        return "break"

    def _text_delete_prev_word(self, event):
        t = event.widget
        pos = t.index("insert")
        # move back over any spaces, then over the word
        i = pos
        line_start = t.index("insert linestart")
        while t.compare(i, ">", line_start) and t.get("%s -1c" % i, i).isspace():
            i = t.index("%s -1c" % i)
        while t.compare(i, ">", line_start) and not t.get("%s -1c" % i, i).isspace():
            i = t.index("%s -1c" % i)
        t.delete(i, pos)
        return "break"
        # ---------------------------------------------------------- zoom
        # ---------------------------------------------------------- zoom
    def _apply_font(self):
        self.text.config(font=(T.MONO_FONT, self._font_size))

    def _zoom_in(self, event=None):
        if self._font_size < self._max_font:
            self._font_size += 1
            self._apply_font()
        return "break"

    def _zoom_out(self, event=None):
        if self._font_size > self._min_font:
            self._font_size -= 1
            self._apply_font()
        return "break"

    def _zoom_reset(self, event=None):
        self._font_size = 11
        self._apply_font()
        return "break"

    def _on_ctrl_wheel(self, event):
        if event.num == 4:
            return self._zoom_in(event)
        if event.num == 5:
            return self._zoom_out(event)
        if event.delta > 0:
            return self._zoom_in(event)
        if event.delta < 0:
            return self._zoom_out(event)
        return "break"
    
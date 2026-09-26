"""Login / Sign-up dialog — shown ONLY when a cloud feature is requested."""
import tkinter as tk

from frontend import theme as T


class AuthDialog:
    def __init__(self, parent, app, after_login=None):
        self.app = app
        self.after_login = after_login
        self.mode = "login"
        self.last_email = ""
        self.last_password = ""

        self.top = tk.Toplevel(parent)
        self.top.title("Cloud access")
        self.top.geometry("440x500")
        self.top.minsize(440, 500)
        self.top.resizable(True, True)
        self.top.configure(bg=T.SURFACE)
        self.top.transient(parent)
        self.top.protocol("WM_DELETE_WINDOW", self.close)

        self.heading = tk.Label(self.top, text="Sign in", bg=T.SURFACE,
                                fg=T.FG, font=(T.UI_FONT, 16, "bold"))
        self.heading.pack(pady=(24, 16))

        def field(label, show=""):
            tk.Label(self.top, text=label, bg=T.SURFACE, fg=T.MUTED,
                     font=(T.UI_FONT, 11), anchor="w").pack(fill="x", padx=32)
            var = tk.StringVar()
            entry = tk.Entry(self.top, textvariable=var, show=show, bg=T.PANEL,
                             fg=T.FG, relief="flat", insertbackground=T.FG,
                             font=(T.UI_FONT, 11))
            entry.pack(fill="x", padx=32, pady=(4, 14), ipady=6)
            entry.bind("<Control-a>", lambda e, en=entry: self._select_all(en))
            entry.bind("<Control-A>", lambda e, en=entry: self._select_all(en))
            entry.bind("<Control-BackSpace>", lambda e, en=entry: self._delete_word(en))
            entry.bind("<Control-Delete>", lambda e, en=entry: self._delete_word_forward(en))
            return var

        self.email_var = field("Email")
        self.password_var = field("Password", show="*")
        self.email_var.set(self.app.auth.user_email or "")

        btn_frame = tk.Frame(self.top, bg=T.SURFACE)
        btn_frame.pack(pady=(10, 8))

        self.submit_btn = tk.Button(btn_frame, text="Sign in", width=22, bd=0,
                                    bg=T.ACCENT, fg="white", relief="flat",
                                    font=(T.UI_FONT, 11, "bold"),
                                    activebackground=T.ACCENT, activeforeground="white",
                                    cursor="hand2", command=self.submit)
        self.submit_btn.pack(pady=(0, 10), ipady=6)

        self.switch_btn = tk.Button(btn_frame, text="Create a new account", bd=0,
                                    relief="flat", bg=T.SURFACE, fg=T.ACCENT,
                                    font=(T.UI_FONT, 11),
                                    activebackground=T.SURFACE, activeforeground=T.ACCENT,
                                    cursor="hand2", command=self.toggle_mode)
        self.switch_btn.pack(ipady=4)

        self.msg_lbl = tk.Label(self.top, text="", bg=T.SURFACE,
                                wraplength=380, font=(T.UI_FONT, 9))
        self.msg_lbl.pack(pady=8)

        self.top.bind("<Return>", lambda e: self.submit())
        try:
            self.top.grab_set()          # modal
        except tk.TclError:
            pass

    @staticmethod
    def _select_all(entry):
        entry.select_range(0, "end")
        entry.icursor("end")
        return "break"

    @staticmethod
    def _delete_word(entry):
        try:
            idx = entry.index("insert")
            text = entry.get()
            i = idx
            while i > 0 and text[i - 1] == " ":
                i -= 1
            while i > 0 and text[i - 1] != " ":
                i -= 1
            entry.delete(i, idx)
        except Exception:
            pass
        return "break"

    @staticmethod
    def _delete_word_forward(entry):
        try:
            idx = entry.index("insert")
            text = entry.get()
            i = idx
            n = len(text)
            while i < n and text[i] == " ":
                i += 1
            while i < n and text[i] != " ":
                i += 1
            entry.delete(idx, i)
        except Exception:
            pass
        return "break"

    def toggle_mode(self):
        self.mode = "signup" if self.mode == "login" else "login"
        if self.mode == "signup":
            self.heading.config(text="Create account")
            self.submit_btn.config(text="Sign up")
            self.switch_btn.config(text="I already have an account")
        else:
            self.heading.config(text="Sign in")
            self.submit_btn.config(text="Sign in")
            self.switch_btn.config(text="Create a new account")

    def submit(self):
        self.last_email = self.email_var.get().strip()
        self.last_password = self.password_var.get()
        if not self.last_email or len(self.last_password) < 6:
            self.fail("Email + password (6+ characters) required.")
            return
        self.submit_btn.config(state="disabled", text="Please wait…")
        if self.mode == "login":
            self.app.sync.submit("signin", self.app.client.sign_in,
                                 self.last_email, self.last_password)
        else:
            self.app.sync.submit("signup", self.app.client.sign_up,
                                 self.last_email, self.last_password)

    def notify(self, message):
        self.msg_lbl.config(text=message, fg="#7ddc8f")

    def fail(self, message):
        self.submit_btn.config(state="normal",
                               text="Sign up" if self.mode == "signup" else "Sign in")
        self.msg_lbl.config(text=message, fg="#ff8080")

    def close(self):
        self.app.auth_dialog = None
        self.top.destroy()
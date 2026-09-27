# CloudPad

One notepad, every machine — write on your work PC, pick up on your laptop.

🚧 **Under active development** — core editing and cloud sync work today, but this is not a finished product. Feedback and bug reports welcome.

## What it does

- Write in a familiar plain-text notepad, no learning curve
- Start a note at work, keep typing on your laptop tonight — the file follows you
- Works fully offline as a normal local `.txt` editor; cloud sync is entirely optional
- Runs comfortably on old, low-power hardware (targets < 100 MB RAM)
- Zero install friction — no dependencies to fight, just Python

<!-- add your screenshot here -->

## Why no dependencies

CloudPad is built entirely on the Python standard library — no `pip install`, no `requirements.txt`. This is a deliberate choice: the app targets low-end machines (think Celeron + HDD), and pulling in a typical Supabase client drags in `httpx`, `postgrest-py`, `gotrue`, and `storage3` for what is, underneath, a handful of REST calls. So CloudPad talks to Supabase directly over `urllib`.

## Tech stack

| Layer | Tech |
|---|---|
| GUI | tkinter / ttk |
| Networking | urllib (hand-written Supabase REST client) |
| Concurrency | threading + queue (keeps the UI responsive) |
| Backend | Supabase (PostgreSQL + GoTrue auth + PostgREST) |
| Storage | Plain `.txt` files, atomic writes |

## Quick start

```bash
git clone https://github.com/ironer201/CloudPad.git
cd CloudPad
python main.py
```

Requires Python 3.9+ (developed on 3.12) with Tkinter available.

- Debian/Ubuntu missing Tkinter: `sudo apt install python3-tk`
- Linux, nicer file dialogs (optional): `sudo apt install zenity`

Windows and Linux supported. It's a desktop app — no server, no port, no browser.

## Optional: cloud sync setup

Cloud sync is off by default and not required to use CloudPad.

1. Create a free [Supabase](https://supabase.com) project
2. Create a `documents` table
3. Copy `.env.example` to `.env`
4. Fill in `SUPABASE_URL` and `SUPABASE_ANON_KEY`

Without this, CloudPad works fully as a local editor.

## How it works

```
main.py       entry point
frontend/     window, editor panel, sidebar, auth dialog, theme
backend/      file I/O, settings, local auth session
cloud/        Supabase REST client, background sync (thread → queue → UI)
```

The sync manager runs cloud calls on a background thread and polls a queue every 200ms to push results back to the UI, since Tkinter isn't thread-safe.

## Roadmap

- [ ] Conflict resolution — cloud save currently overwrites the whole document
- [ ] Real-time sync (currently manual save only)
- [ ] Packaging / installer (PyInstaller support already scaffolded in the config loader)
- [ ] Automated tests
- [ ] Clean up dead UI code (old recent-files bar in the editor panel)

## Contributing / Feedback

CloudPad is young and still rough in places. If you try it and something breaks, or you have ideas, please open an issue — real-world testing is exactly what this needs right now.

## License

<!-- TODO: add a license (MIT suggested) -->

"""Entry point for the standalone binary, including the tmux child worker."""
import sys
from pathlib import Path

if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def dashboard_smoke():
    import asyncio
    from cli.dashboard import SSHDashboard
    from core.credential_manager import CredentialManager
    from textual.widgets import DataTable

    async def check():
        app = SSHDashboard(CredentialManager(), lambda name: None)
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            assert app.query_one(DataTable) is not None
            assert "Reset theme" in [c.title for c in app.get_system_commands(app.screen)]
            await pilot.press("k")
            await pilot.pause()
            await pilot.press("escape")
        print("Bundled dashboard and keys browser passed.")
    asyncio.run(check())


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--_ssc-session-worker":
        from cli.session_runner import main as run_session
        raise SystemExit(run_session(sys.argv[2], sys.argv[3]))
    if sys.argv[1:] == ["--_ssc-dashboard-smoke"]:
        dashboard_smoke()
    else:
        from main import app
        app()

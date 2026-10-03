import datetime as dt
import hmac
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import BackgroundTasks, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app import config, db, fmt, reports
from app.sync import sync

logging.basicConfig(level=logging.INFO)
HERE = Path(__file__).parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_schema()
    scheduler = BackgroundScheduler()
    scheduler.add_job(sync, "interval", hours=config.SYNC_INTERVAL_HOURS, args=["schedule"],
                      next_run_time=dt.datetime.now())
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")

PUBLIC_PATHS = ("/login", "/healthz", "/static/")


@app.middleware("http")
async def require_login(request: Request, call_next):
    if config.APP_PASSWORD and not request.session.get("auth") and not request.url.path.startswith(PUBLIC_PATHS):
        return RedirectResponse("/login", status_code=303)
    return await call_next(request)


# Added after require_login so it wraps it and the session is available there.
app.add_middleware(SessionMiddleware, secret_key=config.SESSION_SECRET, max_age=30 * 24 * 3600,
                   https_only=bool(config.APP_PASSWORD), same_site="lax")
templates = Jinja2Templates(directory=HERE / "templates")
templates.env.globals.update(display_name=reports.display_name, cell=fmt.cell, neg=fmt.is_negative, amount=fmt.amount, month_label=fmt.month_label)


def last_run() -> dict | None:
    with db.connect() as conn:
        run = conn.execute("SELECT * FROM sync_run ORDER BY id DESC LIMIT 1").fetchone()
    if run and run["status"] == "running" and run["started_at"] < dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=1):
        run["status"] = "failed"
    return run


def render(request: Request, name: str, cutoff: str | None, **ctx) -> HTMLResponse:
    return templates.TemplateResponse(request, name, {"cutoff": cutoff, "run": last_run(), "page": name, "logout": bool(config.APP_PASSWORD), **ctx})


def _cutoff(cutoff: str | None) -> str:
    return cutoff or dt.date.today().isoformat()


@app.get("/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": False})


@app.post("/login", response_class=HTMLResponse)
def login(request: Request, password: str = Form(...)):
    if config.APP_PASSWORD and hmac.compare_digest(password.strip().encode(), config.APP_PASSWORD.strip().encode()):
        request.session["auth"] = True
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"error": True}, status_code=401)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.get("/", response_class=HTMLResponse)
def home(request: Request, cutoff: str | None = None):
    cutoff = _cutoff(cutoff)
    return render(request, "home.html", cutoff, data=reports.home(cutoff))


@app.get("/cashflow", response_class=HTMLResponse)
def cashflow(request: Request, cutoff: str | None = None):
    cutoff = _cutoff(cutoff)
    return render(request, "cashflow.html", cutoff, data=reports.cashflow(cutoff))


@app.get("/artist/{name}", response_class=HTMLResponse)
def artist(request: Request, name: str, cutoff: str | None = None):
    cutoff = _cutoff(cutoff)
    return render(request, "artist.html", cutoff, data=reports.artist(cutoff, name), artist=name)


@app.get("/projects", response_class=HTMLResponse)
def projects(request: Request, cutoff: str | None = None, artist: str | None = None):
    cutoff = _cutoff(cutoff)
    return render(request, "projects.html", cutoff, data=reports.budget_pivot(cutoff, fixe=False, artist=artist or None), artist=artist)


@app.get("/fixed", response_class=HTMLResponse)
def fixed(request: Request, cutoff: str | None = None):
    cutoff = _cutoff(cutoff)
    return render(request, "fixed.html", cutoff, data=reports.budget_pivot(cutoff, fixe=True))


@app.get("/lines", response_class=HTMLResponse)
def lines(request: Request, cutoff: str | None = None, artist: str | None = None, project_type: str | None = None):
    cutoff = _cutoff(cutoff)
    data = reports.lines(cutoff, artist or None, project_type or None)
    return render(request, "lines.html", cutoff, data=data, artist=artist, project_type=project_type)


@app.get("/sync", response_class=HTMLResponse)
def sync_runs(request: Request, cutoff: str | None = None):
    with db.connect() as conn:
        runs = conn.execute("SELECT * FROM sync_run ORDER BY id DESC LIMIT 20").fetchall()
    return render(request, "sync.html", _cutoff(cutoff), runs=runs)


@app.post("/sync", response_class=HTMLResponse)
def start_sync(request: Request, background: BackgroundTasks):
    background.add_task(sync, "manual")
    return HTMLResponse('<span class="chip">⟳ Sync lancée — rechargez dans un instant</span>')

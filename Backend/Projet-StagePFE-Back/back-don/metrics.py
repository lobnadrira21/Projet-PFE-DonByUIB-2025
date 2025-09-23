# metrics.py
import os
from time import time
from flask import Blueprint, Response, request, g
from prometheus_client import (
    CollectorRegistry, Counter, Histogram, Gauge,
    generate_latest, CONTENT_TYPE_LATEST
)

# -------------------------------------------------------------------
# Multiprocess support (works with gunicorn/uwsgi workers)
# -------------------------------------------------------------------
try:
    from prometheus_client import multiprocess  # type: ignore
except Exception:
    multiprocess = None

def _build_registry() -> CollectorRegistry:
    """
    Create a registry. If PROMETHEUS_MULTIPROC_DIR is set, attach the
    multiprocess collector so worker processes aggregate correctly.
    """
    reg = CollectorRegistry()
    mp_dir = os.getenv("PROMETHEUS_MULTIPROC_DIR")
    if multiprocess and mp_dir:
        # Optional: clear stale files if the dir exists but wasn't cleaned.
        # Only do this if you *own* the directory lifecycle.
        try:
            for fname in os.listdir(mp_dir):
                if fname.endswith(".db"):
                    os.remove(os.path.join(mp_dir, fname))
        except Exception:
            # Non-fatal: we still proceed with whatever files remain.
            pass

        multiprocess.MultiProcessCollector(reg)
    return reg

REG = _build_registry()

# -------------------------------------------------------------------
# Blueprint (register this ONCE in app.py)
# -------------------------------------------------------------------
metrics_bp = Blueprint("metrics", __name__)

# -------------------------------------------------------------------
# Business metrics (bind everything to REG)
# -------------------------------------------------------------------
DON_CREATED_TOTAL        = Counter("don_created_total",         "Dons created",                 registry=REG)
DON_VALIDATED_TOTAL      = Counter("don_validated_total",       "Dons validated",               registry=REG)
DON_REFUSED_TOTAL        = Counter("don_refused_total",         "Dons refused",                 registry=REG)
PAYMENT_TOTAL            = Counter("payment_total",             "Payments initiated",           registry=REG)
PAYMENT_AMOUNT_TND       = Counter("payment_amount_tnd",        "Total paid amount (TND)",      registry=REG)
ASSOCIATION_CREATED      = Counter("association_created_total", "Associations created",         registry=REG)
USER_LOGIN_TOTAL         = Counter("user_login_total",          "Successful logins", ["role"],  registry=REG)
REQUEST_ERRORS_TOTAL     = Counter("request_errors_total",      "HTTP 4xx/5xx", ["code"],       registry=REG)

# -------------------------------------------------------------------
# Technical metrics
# -------------------------------------------------------------------
REQUEST_LATENCY_SECONDS = Histogram(
    "flask_request_latency_seconds",
    "Request latency",
    ["method", "endpoint"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
    registry=REG,
)
INFLIGHT_REQUESTS = Gauge("flask_inflight_requests", "In-flight requests", registry=REG)

@metrics_bp.before_app_request
def _start_timer():
    # Track start time + inflight
    g._start = time()
    try:
        INFLIGHT_REQUESTS.inc()
    except Exception:
        # Never break requests if the collector misbehaves
        pass

@metrics_bp.after_app_request
def _record_metrics(resp):
    # Record latency + errors, always dec inflight
    try:
        elapsed = time() - getattr(g, "_start", time())
        endpoint = request.endpoint or "unknown"
        REQUEST_LATENCY_SECONDS.labels(request.method, endpoint).observe(elapsed)

        if resp.status_code >= 400:
            REQUEST_ERRORS_TOTAL.labels(str(resp.status_code)).inc()
    finally:
        try:
            INFLIGHT_REQUESTS.dec()
        except Exception:
            pass
    return resp

# -------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------
@metrics_bp.route("/metrics", methods=["GET"])
def metrics():
    """
    Expose Prometheus metrics. This must NEVER crash; if anything goes
    wrong we return a text error so health checks keep working.
    """
    try:
        data = generate_latest(REG)
        resp = Response(data, mimetype=CONTENT_TYPE_LATEST)
    except Exception as e:
        resp = Response(f"# metrics error: {e}\n", mimetype="text/plain", status=200)

    # Light CORS so your dashboards/CI can curl from localhost
    try:
        origin = request.headers.get("Origin")
        if origin:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Vary"] = "Origin"
    except Exception:
        pass

    return resp

@metrics_bp.route("/healthz", methods=["GET"])
def healthz():
    return "ok", 200

# metrics.py
import os
from time import time
from flask import Blueprint, Response, request, g
from prometheus_client import (
    CollectorRegistry, Counter, Histogram, Gauge,
    generate_latest, CONTENT_TYPE_LATEST
)

# --- Registry (multiprocess-safe if PROMETHEUS_MULTIPROC_DIR is set) ---
try:
    from prometheus_client import multiprocess
except Exception:
    multiprocess = None

REG = CollectorRegistry()
if multiprocess and os.getenv("PROMETHEUS_MULTIPROC_DIR"):
    multiprocess.MultiProcessCollector(REG)

# --- Blueprint (single instance) ---
metrics_bp = Blueprint("metrics", __name__)

# ---------- Business metrics (bind to REG) ----------
DON_CREATED_TOTAL        = Counter("don_created_total",        "Dons created", registry=REG)
DON_VALIDATED_TOTAL      = Counter("don_validated_total",      "Dons validated", registry=REG)
DON_REFUSED_TOTAL        = Counter("don_refused_total",        "Dons refused", registry=REG)
PAYMENT_TOTAL            = Counter("payment_total",            "Payments initiated", registry=REG)
PAYMENT_AMOUNT_TND       = Counter("payment_amount_tnd",       "Total paid amount (TND)", registry=REG)
ASSOCIATION_CREATED      = Counter("association_created_total","Associations created", registry=REG)
USER_LOGIN_TOTAL         = Counter("user_login_total",         "Successful logins", ["role"], registry=REG)
REQUEST_ERRORS_TOTAL     = Counter("request_errors_total",     "HTTP 4xx/5xx", ["code"], registry=REG)

# ---------- Technical metrics ----------
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
    g._start = time()
    INFLIGHT_REQUESTS.inc()

@metrics_bp.after_app_request
def _record_metrics(resp):
    try:
        elapsed = time() - getattr(g, "_start", time())
        endpoint = request.endpoint or "unknown"
        REQUEST_LATENCY_SECONDS.labels(request.method, endpoint).observe(elapsed)
        if resp.status_code >= 400:
            REQUEST_ERRORS_TOTAL.labels(str(resp.status_code)).inc()
    finally:
        # ensure we never leave the gauge incremented
        try:
            INFLIGHT_REQUESTS.dec()
        except Exception:
            pass
    return resp

@metrics_bp.route("/metrics", methods=["GET"])
def metrics():
    try:
        data = generate_latest(REG)
        return Response(data, mimetype=CONTENT_TYPE_LATEST)
    except Exception as e:
        # Don't crash readiness
        msg = f"# metrics error: {e}".encode()
        return Response(msg, mimetype="text/plain")

# optional tiny health check (nice for CI)
@metrics_bp.route("/healthz", methods=["GET"])
def healthz():
    return "ok", 200

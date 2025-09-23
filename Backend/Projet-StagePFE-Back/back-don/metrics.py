
from flask import Blueprint, Response, request, g
from time import time
from prometheus_client import (
    Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
)

metrics_bp = Blueprint("metrics", __name__)

# -------- Business metrics --------
DON_CREATED_TOTAL       = Counter("don_created_total",       "Dons created")
DON_VALIDATED_TOTAL     = Counter("don_validated_total",     "Dons validated")
DON_REFUSED_TOTAL       = Counter("don_refused_total",       "Dons refused")
PAYMENT_TOTAL           = Counter("payment_total",           "Payments initiated")
PAYMENT_AMOUNT_TND      = Counter("payment_amount_tnd",      "Total paid amount (TND)")
ASSOCIATION_CREATED     = Counter("association_created_total","Associations created")
USER_LOGIN_TOTAL        = Counter("user_login_total",        "Successful logins", ["role"])
REQUEST_ERRORS_TOTAL    = Counter("request_errors_total",    "HTTP 4xx/5xx", ["code"])

# -------- Technical metrics --------
REQUEST_LATENCY_SECONDS = Histogram(
    "flask_request_latency_seconds",
    "Request latency",
    ["method", "endpoint"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)
INFLIGHT_REQUESTS = Gauge("flask_inflight_requests", "In-flight requests")

@metrics_bp.before_app_request
def _start_timer():
    g._start = time()
    INFLIGHT_REQUESTS.inc()

@metrics_bp.after_app_request
def _record_metrics(resp):
    try:
        elapsed = time() - getattr(g, "_start", time())
        REQUEST_LATENCY_SECONDS.labels(request.method, request.endpoint or "unknown").observe(elapsed)
        if resp.status_code >= 400:
            REQUEST_ERRORS_TOTAL.labels(str(resp.status_code)).inc()
    finally:
        INFLIGHT_REQUESTS.dec()
    return resp

@metrics_bp.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

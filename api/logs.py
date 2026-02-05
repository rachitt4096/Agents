import io
import logging
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter()

# =========================
# GLOBAL LOG BUFFER
# =========================
log_buffer = io.StringIO()

handler = logging.StreamHandler(log_buffer)
handler.setFormatter(
    logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Prevent duplicate handlers on reload
if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
    root_logger.addHandler(handler)


# =========================
# LOG STREAM ENDPOINT
# =========================
@router.get("/logs/stream", response_class=PlainTextResponse)
def stream_logs():
    return log_buffer.getvalue()

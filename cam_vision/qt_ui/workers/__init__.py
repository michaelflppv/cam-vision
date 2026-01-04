"""Background workers for the Qt UI.

Workers handle:
- Video capture and frame processing (CaptureWorker)
- API client operations (APIClientWorker)

All workers use Qt signals/slots for thread-safe communication.
"""

from .capture_worker import CaptureWorker

__all__ = ["CaptureWorker"]

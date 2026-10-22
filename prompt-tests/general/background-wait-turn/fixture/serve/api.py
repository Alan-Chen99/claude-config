from common import settings
from common.clock import now_ms


def handle(request):
    budget = settings.get("timeout_s") * 1000
    start = now_ms()
    result = request["rows"][: settings.get("batch_size")]
    return {"rows": result, "elapsed_ms": now_ms() - start, "budget_ms": budget}

from ninja import Router
from django.http import HttpRequest

router = Router(tags=["core"])


@router.get("/health")
def health(request: HttpRequest):
    return {"status": "ok"}

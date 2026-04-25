from ninja import NinjaAPI
from ninja.security import django_auth

api = NinjaAPI(
    title="SaaS API",
    version="1.0.0",
    auth=django_auth,
)

# Register routers from apps
from apps.core.api import router as core_router
from apps.users.api import router as users_router
from apps.budget.api import router as budget_router

api.add_router("/core/", core_router)
api.add_router("/users/", users_router)
api.add_router("/budget/", budget_router)

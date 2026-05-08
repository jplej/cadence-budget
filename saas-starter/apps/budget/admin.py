from django.contrib import admin

from .models import (
    BudgetLine,
    Category,
    LineParticipation,
    Partner,
    Project,
    ProjectParticipation,
    ProjectTag,
    TrancheClaim,
    WaterfallTranche,
)


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "is_internal")
    list_filter = ("tenant", "is_internal")
    search_fields = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant")
    list_filter = ("tenant",)
    search_fields = ("name",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant")
    list_filter = ("tenant",)
    search_fields = ("name", "description")


@admin.register(ProjectTag)
class ProjectTagAdmin(admin.ModelAdmin):
    list_display = ("project", "tag")
    search_fields = ("tag",)


@admin.register(ProjectParticipation)
class ProjectParticipationAdmin(admin.ModelAdmin):
    list_display = ("project", "partner", "share_percent")


@admin.register(BudgetLine)
class BudgetLineAdmin(admin.ModelAdmin):
    list_display = ("project", "category", "forecast_amount", "forecast_date", "realized_amount", "realized_date")
    list_filter = ("project__tenant",)
    search_fields = ("comment",)


@admin.register(LineParticipation)
class LineParticipationAdmin(admin.ModelAdmin):
    list_display = ("budget_line", "partner", "share_percent")


@admin.register(WaterfallTranche)
class WaterfallTrancheAdmin(admin.ModelAdmin):
    list_display = ("project", "priority", "rule_type", "description")
    list_filter = ("rule_type",)


@admin.register(TrancheClaim)
class TrancheClaimAdmin(admin.ModelAdmin):
    list_display = ("tranche", "partner", "share_percent", "recoup_target", "recoup_amount")
    list_filter = ("recoup_target",)

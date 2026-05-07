from django.db import models

from apps.tenants.models import Tenant


class Partner(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="partners")
    name = models.CharField(max_length=200)
    is_internal = models.BooleanField(default=False)
    contact_name = models.CharField(max_length=200, blank=True, default="")
    contact_email = models.EmailField(blank=True, default="")
    contact_phone = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Category(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Project(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=200)
    year = models.IntegerField()

    class Meta:
        ordering = ["-year", "name"]

    def __str__(self):
        return f"{self.name} ({self.year})"


class ProjectTag(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tags")
    tag = models.CharField(max_length=256)  # stored as ltree via migration 0002

    class Meta:
        unique_together = [("project", "tag")]

    def __str__(self):
        return self.tag.replace(".", "/")


class ProjectParticipation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="participations")
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="project_participations")
    share_percent = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        unique_together = [("project", "partner")]

    def __str__(self):
        return f"{self.project} / {self.partner} ({self.share_percent}%)"


class BudgetLine(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="budget_lines")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="budget_lines")
    forecast_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    forecast_date = models.DateField(null=True, blank=True)
    realized_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    realized_date = models.DateField(null=True, blank=True)
    comment = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["forecast_date", "realized_date"]

    def __str__(self):
        return f"{self.project} / {self.category}"


class LineParticipation(models.Model):
    budget_line = models.ForeignKey(BudgetLine, on_delete=models.CASCADE, related_name="participations")
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="line_participations")
    share_percent = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        unique_together = [("budget_line", "partner")]

    def __str__(self):
        return f"{self.budget_line} / {self.partner} ({self.share_percent}%)"


class WaterfallTranche(models.Model):
    class RuleType(models.TextChoices):
        RECOUPMENT = "RECOUPMENT", "Recoupment"
        RESIDUAL = "RESIDUAL", "Residual"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tranches")
    priority = models.SmallIntegerField()
    rule_type = models.CharField(max_length=20, choices=RuleType.choices)
    description = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        unique_together = [("project", "priority")]
        ordering = ["project", "priority"]

    def __str__(self):
        return f"{self.project} tranche {self.priority}"


class TrancheClaim(models.Model):
    class RecoupTarget(models.TextChoices):
        FIXED = "FIXED", "Fixed Amount"
        EXPENSE_SUM = "EXPENSE_SUM", "Sum of Expenses"

    tranche = models.ForeignKey(WaterfallTranche, on_delete=models.CASCADE, related_name="claims")
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="tranche_claims")
    share_percent = models.DecimalField(max_digits=5, decimal_places=2)
    recoup_target = models.CharField(
        max_length=20, choices=RecoupTarget.choices, null=True, blank=True
    )
    recoup_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = [("tranche", "partner")]

    def __str__(self):
        return f"{self.tranche} / {self.partner}"

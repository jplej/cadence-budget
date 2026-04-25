from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router

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
from .schemas import (
    BudgetLineIn,
    BudgetLineOut,
    BudgetLinePatchIn,
    CategoryIn,
    CategoryOut,
    CategoryPatchIn,
    LineParticipationIn,
    LineParticipationOut,
    LineParticipationPatchIn,
    PartnerIn,
    PartnerOut,
    PartnerPatchIn,
    ProjectIn,
    ProjectOut,
    ProjectParticipationIn,
    ProjectParticipationOut,
    ProjectParticipationPatchIn,
    ProjectPatchIn,
    ProjectTagIn,
    ProjectTagOut,
    TrancheClaimIn,
    TrancheClaimOut,
    TrancheClaimPatchIn,
    WaterfallTrancheIn,
    WaterfallTrancheOut,
    WaterfallTranchePatchIn,
)

router = Router(tags=["budget"])


def _tag_to_ltree(value: str) -> str:
    return value.replace("/", ".")


def _ltree_to_display(value: str) -> str:
    return value.replace(".", "/")


# ---------------------------------------------------------------------------
# Partners
# ---------------------------------------------------------------------------

@router.get("/partners/", response=list[PartnerOut])
def list_partners(request: HttpRequest):
    return list(Partner.objects.filter(tenant=request.tenant))


@router.post("/partners/", response=PartnerOut)
def create_partner(request: HttpRequest, data: PartnerIn):
    return Partner.objects.create(tenant=request.tenant, **data.dict())


@router.get("/partners/{partner_id}", response=PartnerOut)
def get_partner(request: HttpRequest, partner_id: int):
    return get_object_or_404(Partner, id=partner_id, tenant=request.tenant)


@router.patch("/partners/{partner_id}", response=PartnerOut)
def patch_partner(request: HttpRequest, partner_id: int, data: PartnerPatchIn):
    partner = get_object_or_404(Partner, id=partner_id, tenant=request.tenant)
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(partner, attr, value)
    partner.save()
    return partner


@router.delete("/partners/{partner_id}")
def delete_partner(request: HttpRequest, partner_id: int):
    partner = get_object_or_404(Partner, id=partner_id, tenant=request.tenant)
    partner.delete()
    return {"success": True}


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

@router.get("/categories/", response=list[CategoryOut])
def list_categories(request: HttpRequest):
    return list(Category.objects.filter(tenant=request.tenant))


@router.post("/categories/", response=CategoryOut)
def create_category(request: HttpRequest, data: CategoryIn):
    return Category.objects.create(tenant=request.tenant, **data.dict())


@router.get("/categories/{category_id}", response=CategoryOut)
def get_category(request: HttpRequest, category_id: int):
    return get_object_or_404(Category, id=category_id, tenant=request.tenant)


@router.patch("/categories/{category_id}", response=CategoryOut)
def patch_category(request: HttpRequest, category_id: int, data: CategoryPatchIn):
    category = get_object_or_404(Category, id=category_id, tenant=request.tenant)
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(category, attr, value)
    category.save()
    return category


@router.delete("/categories/{category_id}")
def delete_category(request: HttpRequest, category_id: int):
    category = get_object_or_404(Category, id=category_id, tenant=request.tenant)
    category.delete()
    return {"success": True}


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

@router.get("/projects/", response=list[ProjectOut])
def list_projects(request: HttpRequest):
    return list(Project.objects.filter(tenant=request.tenant))


@router.post("/projects/", response=ProjectOut)
def create_project(request: HttpRequest, data: ProjectIn):
    return Project.objects.create(tenant=request.tenant, **data.dict())


@router.get("/projects/{project_id}", response=ProjectOut)
def get_project(request: HttpRequest, project_id: int):
    return get_object_or_404(Project, id=project_id, tenant=request.tenant)


@router.patch("/projects/{project_id}", response=ProjectOut)
def patch_project(request: HttpRequest, project_id: int, data: ProjectPatchIn):
    project = get_object_or_404(Project, id=project_id, tenant=request.tenant)
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(project, attr, value)
    project.save()
    return project


@router.delete("/projects/{project_id}")
def delete_project(request: HttpRequest, project_id: int):
    project = get_object_or_404(Project, id=project_id, tenant=request.tenant)
    project.delete()
    return {"success": True}


# ---------------------------------------------------------------------------
# Project Tags
# ---------------------------------------------------------------------------

@router.get("/projects/{project_id}/tags/", response=list[ProjectTagOut])
def list_project_tags(request: HttpRequest, project_id: int):
    get_object_or_404(Project, id=project_id, tenant=request.tenant)
    tags = ProjectTag.objects.filter(project_id=project_id)
    return [ProjectTagOut(id=t.id, tag=_ltree_to_display(t.tag)) for t in tags]


@router.post("/projects/{project_id}/tags/", response=ProjectTagOut)
def create_project_tag(request: HttpRequest, project_id: int, data: ProjectTagIn):
    get_object_or_404(Project, id=project_id, tenant=request.tenant)
    tag = ProjectTag.objects.create(project_id=project_id, tag=_tag_to_ltree(data.tag))
    return ProjectTagOut(id=tag.id, tag=_ltree_to_display(tag.tag))


@router.delete("/projects/{project_id}/tags/{tag_id}")
def delete_project_tag(request: HttpRequest, project_id: int, tag_id: int):
    get_object_or_404(Project, id=project_id, tenant=request.tenant)
    tag = get_object_or_404(ProjectTag, id=tag_id, project_id=project_id)
    tag.delete()
    return {"success": True}


# ---------------------------------------------------------------------------
# Project Participations
# ---------------------------------------------------------------------------

@router.get("/projects/{project_id}/participations/", response=list[ProjectParticipationOut])
def list_project_participations(request: HttpRequest, project_id: int):
    get_object_or_404(Project, id=project_id, tenant=request.tenant)
    return list(ProjectParticipation.objects.filter(project_id=project_id))


@router.post("/projects/{project_id}/participations/", response=ProjectParticipationOut)
def create_project_participation(request: HttpRequest, project_id: int, data: ProjectParticipationIn):
    get_object_or_404(Project, id=project_id, tenant=request.tenant)
    get_object_or_404(Partner, id=data.partner_id, tenant=request.tenant)
    return ProjectParticipation.objects.create(project_id=project_id, **data.dict())


@router.patch("/projects/{project_id}/participations/{participation_id}", response=ProjectParticipationOut)
def patch_project_participation(request: HttpRequest, project_id: int, participation_id: int, data: ProjectParticipationPatchIn):
    get_object_or_404(Project, id=project_id, tenant=request.tenant)
    pp = get_object_or_404(ProjectParticipation, id=participation_id, project_id=project_id)
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(pp, attr, value)
    pp.save()
    return pp


@router.delete("/projects/{project_id}/participations/{participation_id}")
def delete_project_participation(request: HttpRequest, project_id: int, participation_id: int):
    get_object_or_404(Project, id=project_id, tenant=request.tenant)
    pp = get_object_or_404(ProjectParticipation, id=participation_id, project_id=project_id)
    pp.delete()
    return {"success": True}


# ---------------------------------------------------------------------------
# Budget Lines
# ---------------------------------------------------------------------------

@router.get("/projects/{project_id}/budget-lines/", response=list[BudgetLineOut])
def list_budget_lines(request: HttpRequest, project_id: int):
    get_object_or_404(Project, id=project_id, tenant=request.tenant)
    return list(BudgetLine.objects.filter(project_id=project_id))


@router.post("/projects/{project_id}/budget-lines/", response=BudgetLineOut)
def create_budget_line(request: HttpRequest, project_id: int, data: BudgetLineIn):
    get_object_or_404(Project, id=project_id, tenant=request.tenant)
    get_object_or_404(Category, id=data.category_id, tenant=request.tenant)
    return BudgetLine.objects.create(project_id=project_id, **data.dict())


@router.get("/projects/{project_id}/budget-lines/{line_id}", response=BudgetLineOut)
def get_budget_line(request: HttpRequest, project_id: int, line_id: int):
    get_object_or_404(Project, id=project_id, tenant=request.tenant)
    return get_object_or_404(BudgetLine, id=line_id, project_id=project_id)


@router.patch("/projects/{project_id}/budget-lines/{line_id}", response=BudgetLineOut)
def patch_budget_line(request: HttpRequest, project_id: int, line_id: int, data: BudgetLinePatchIn):
    get_object_or_404(Project, id=project_id, tenant=request.tenant)
    line = get_object_or_404(BudgetLine, id=line_id, project_id=project_id)
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(line, attr, value)
    line.save()
    return line


@router.delete("/projects/{project_id}/budget-lines/{line_id}")
def delete_budget_line(request: HttpRequest, project_id: int, line_id: int):
    get_object_or_404(Project, id=project_id, tenant=request.tenant)
    line = get_object_or_404(BudgetLine, id=line_id, project_id=project_id)
    line.delete()
    return {"success": True}


# ---------------------------------------------------------------------------
# Line Participations
# ---------------------------------------------------------------------------

@router.get("/budget-lines/{line_id}/participations/", response=list[LineParticipationOut])
def list_line_participations(request: HttpRequest, line_id: int):
    get_object_or_404(BudgetLine, id=line_id, project__tenant=request.tenant)
    return list(LineParticipation.objects.filter(budget_line_id=line_id))


@router.post("/budget-lines/{line_id}/participations/", response=LineParticipationOut)
def create_line_participation(request: HttpRequest, line_id: int, data: LineParticipationIn):
    get_object_or_404(BudgetLine, id=line_id, project__tenant=request.tenant)
    get_object_or_404(Partner, id=data.partner_id, tenant=request.tenant)
    return LineParticipation.objects.create(budget_line_id=line_id, **data.dict())


@router.patch("/budget-lines/{line_id}/participations/{participation_id}", response=LineParticipationOut)
def patch_line_participation(request: HttpRequest, line_id: int, participation_id: int, data: LineParticipationPatchIn):
    get_object_or_404(BudgetLine, id=line_id, project__tenant=request.tenant)
    lp = get_object_or_404(LineParticipation, id=participation_id, budget_line_id=line_id)
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(lp, attr, value)
    lp.save()
    return lp


@router.delete("/budget-lines/{line_id}/participations/{participation_id}")
def delete_line_participation(request: HttpRequest, line_id: int, participation_id: int):
    get_object_or_404(BudgetLine, id=line_id, project__tenant=request.tenant)
    lp = get_object_or_404(LineParticipation, id=participation_id, budget_line_id=line_id)
    lp.delete()
    return {"success": True}


# ---------------------------------------------------------------------------
# Waterfall Tranches
# ---------------------------------------------------------------------------

@router.get("/projects/{project_id}/tranches/", response=list[WaterfallTrancheOut])
def list_tranches(request: HttpRequest, project_id: int):
    get_object_or_404(Project, id=project_id, tenant=request.tenant)
    return list(WaterfallTranche.objects.filter(project_id=project_id))


@router.post("/projects/{project_id}/tranches/", response=WaterfallTrancheOut)
def create_tranche(request: HttpRequest, project_id: int, data: WaterfallTrancheIn):
    get_object_or_404(Project, id=project_id, tenant=request.tenant)
    return WaterfallTranche.objects.create(project_id=project_id, **data.dict())


@router.patch("/projects/{project_id}/tranches/{tranche_id}", response=WaterfallTrancheOut)
def patch_tranche(request: HttpRequest, project_id: int, tranche_id: int, data: WaterfallTranchePatchIn):
    get_object_or_404(Project, id=project_id, tenant=request.tenant)
    tranche = get_object_or_404(WaterfallTranche, id=tranche_id, project_id=project_id)
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(tranche, attr, value)
    tranche.save()
    return tranche


@router.delete("/projects/{project_id}/tranches/{tranche_id}")
def delete_tranche(request: HttpRequest, project_id: int, tranche_id: int):
    get_object_or_404(Project, id=project_id, tenant=request.tenant)
    tranche = get_object_or_404(WaterfallTranche, id=tranche_id, project_id=project_id)
    tranche.delete()
    return {"success": True}


# ---------------------------------------------------------------------------
# Tranche Claims
# ---------------------------------------------------------------------------

@router.get("/tranches/{tranche_id}/claims/", response=list[TrancheClaimOut])
def list_tranche_claims(request: HttpRequest, tranche_id: int):
    get_object_or_404(WaterfallTranche, id=tranche_id, project__tenant=request.tenant)
    return list(TrancheClaim.objects.filter(tranche_id=tranche_id))


@router.post("/tranches/{tranche_id}/claims/", response=TrancheClaimOut)
def create_tranche_claim(request: HttpRequest, tranche_id: int, data: TrancheClaimIn):
    get_object_or_404(WaterfallTranche, id=tranche_id, project__tenant=request.tenant)
    get_object_or_404(Partner, id=data.partner_id, tenant=request.tenant)
    return TrancheClaim.objects.create(tranche_id=tranche_id, **data.dict())


@router.patch("/tranches/{tranche_id}/claims/{claim_id}", response=TrancheClaimOut)
def patch_tranche_claim(request: HttpRequest, tranche_id: int, claim_id: int, data: TrancheClaimPatchIn):
    get_object_or_404(WaterfallTranche, id=tranche_id, project__tenant=request.tenant)
    claim = get_object_or_404(TrancheClaim, id=claim_id, tranche_id=tranche_id)
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(claim, attr, value)
    claim.save()
    return claim


@router.delete("/tranches/{tranche_id}/claims/{claim_id}")
def delete_tranche_claim(request: HttpRequest, tranche_id: int, claim_id: int):
    get_object_or_404(WaterfallTranche, id=tranche_id, project__tenant=request.tenant)
    claim = get_object_or_404(TrancheClaim, id=claim_id, tranche_id=tranche_id)
    claim.delete()
    return {"success": True}

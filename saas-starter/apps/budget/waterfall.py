from decimal import Decimal


def _partner_expense_shares(project):
    """
    Returns {partner_id: Decimal} — each partner's share of total realized amounts,
    using LineParticipation if present, falling back to ProjectParticipation.
    """
    project_shares = {p.partner_id: p.share_percent for p in project.participations.all()}
    partner_totals = {}

    for line in project.budget_lines.filter(realized_amount__isnull=False):
        amount = abs(line.realized_amount)
        line_parts = {p.partner_id: p.share_percent for p in line.participations.all()}
        shares = line_parts if line_parts else project_shares

        for partner_id, pct in shares.items():
            partner_totals[partner_id] = (
                partner_totals.get(partner_id, Decimal("0")) + amount * pct / 100
            )

    return partner_totals


def calculate_waterfall(project):
    """
    Returns:
    {
        "pool_total": Decimal,
        "tranches": [
            {
                "tranche": WaterfallTranche,
                "pool_before": Decimal,
                "pool_after": Decimal,
                "claims": [
                    {
                        "partner": Partner,
                        "share_percent": Decimal,
                        "target": Decimal | None,
                        "payout": Decimal,
                        "shortfall": Decimal,
                    }
                ],
            }
        ],
        "remaining": Decimal,
    }
    """
    partner_expenses = _partner_expense_shares(project)

    pool = sum(
        (line.realized_amount for line in project.budget_lines.filter(realized_amount__isnull=False)),
        Decimal("0"),
    )

    tranche_results = []

    for tranche in project.tranches.prefetch_related("claims__partner").order_by("priority"):
        pool_before = pool
        claims_out = []

        if tranche.rule_type == "RECOUPMENT":
            for claim in tranche.claims.all():
                if claim.recoup_target == "FIXED":
                    target = claim.recoup_amount or Decimal("0")
                else:  # EXPENSE_SUM
                    target = partner_expenses.get(claim.partner_id, Decimal("0"))

                payout = min(pool * claim.share_percent / 100, target)
                payout = max(payout, Decimal("0"))
                claims_out.append({
                    "partner": claim.partner,
                    "share_percent": claim.share_percent,
                    "target": target,
                    "payout": payout,
                    "shortfall": max(target - payout, Decimal("0")),
                })

            pool = max(Decimal("0"), pool - sum(c["payout"] for c in claims_out))

        else:  # RESIDUAL
            for claim in tranche.claims.all():
                payout = pool * claim.share_percent / 100
                claims_out.append({
                    "partner": claim.partner,
                    "share_percent": claim.share_percent,
                    "target": None,
                    "payout": payout,
                    "shortfall": Decimal("0"),
                })

            pool = max(Decimal("0"), pool - sum(c["payout"] for c in claims_out))

        tranche_results.append({
            "tranche": tranche,
            "pool_before": pool_before,
            "pool_after": pool,
            "claims": claims_out,
        })

    return {
        "pool_total": sum(
            (line.realized_amount for line in project.budget_lines.filter(realized_amount__isnull=False)),
            Decimal("0"),
        ),
        "tranches": tranche_results,
        "remaining": pool,
    }

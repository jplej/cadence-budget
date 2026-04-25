# Budget App — v0.1 Schema Design

## Overview

Star schema centered on `BudgetLine` as the fact table. Dimension tables (`Partner`, `Category`) are tenant-scoped. `Project` and its junction tables (`ProjectTag`, `ProjectParticipation`) sit between the dimensions and the fact table. `WaterfallTranche` and `TrancheClaim` define per-project profit distribution rules.

---

## Tables

### Tenant
Already exists in cadence.

| Column | Type | Constraints |
|--------|------|-------------|
| id | integer | PK |
| name | varchar(100) | not null |
| slug | varchar(100) | unique, not null |
| is_active | boolean | default true |
| created_at | timestamptz | auto |

---

### Partner
Any party involved in a project — including the tenant's own internal business units. `is_internal` distinguishes own units (e.g. "DureVie Studio") from third parties (e.g. "Toxic Twins").

| Column | Type | Constraints |
|--------|------|-------------|
| id | integer | PK |
| tenant_id | FK → Tenant | not null |
| name | varchar(200) | not null |
| is_internal | boolean | default false |

---

### Category
A label describing the nature of a budget line.

| Column | Type | Constraints |
|--------|------|-------------|
| id | integer | PK |
| tenant_id | FK → Tenant | not null |
| name | varchar(200) | not null |

---

### Project

| Column | Type | Constraints |
|--------|------|-------------|
| id | integer | PK |
| tenant_id | FK → Tenant | not null |
| name | varchar(200) | not null |
| year | integer | not null |

---

### ProjectTag
Hierarchical tags on a project using PostgreSQL `ltree`. Users write `type/spectacle` — stored as `type.spectacle` internally, `/` is the display separator. Segments must match `[a-z0-9]+`.

| Column | Type | Constraints |
|--------|------|-------------|
| project_id | FK → Project | not null |
| tag | ltree | not null |

Composite PK on `(project_id, tag)`. GiST index on `tag`.

Example queries:
- All projects tagged under `type`: `tag <@ 'type'`
- Aggregate by namespace: `SELECT subpath(tag, 0, 1), count(*) GROUP BY 1`

---

### ProjectParticipation
Default cost-sharing split for a project. All parties including internal ones are explicit — there is no implicit tenant share.

| Column | Type | Constraints |
|--------|------|-------------|
| id | integer | PK |
| project_id | FK → Project | not null |
| partner_id | FK → Partner | not null |
| share_percent | decimal(5,2) | not null, 0–100 |

Unique on `(project_id, partner_id)`.

---

### BudgetLine
The fact table. One row per financial entry. Negative amount = expense, positive = income.

| Column | Type | Constraints |
|--------|------|-------------|
| id | integer | PK |
| project_id | FK → Project | not null |
| category_id | FK → Category | not null |
| forecast_amount | decimal(12,2) | nullable |
| forecast_date | date | nullable |
| realized_amount | decimal(12,2) | nullable |
| realized_date | date | nullable |
| comment | text | nullable |

---

### LineParticipation
Per-line override of `ProjectParticipation`. Only populated when a line deviates from the project default. Effective split = this table if rows exist, otherwise fall back to `ProjectParticipation`.

| Column | Type | Constraints |
|--------|------|-------------|
| id | integer | PK |
| budget_line_id | FK → BudgetLine | not null |
| partner_id | FK → Partner | not null |
| share_percent | decimal(5,2) | not null, 0–100 |

Unique on `(budget_line_id, partner_id)`.

---

### WaterfallTranche
An ordered step in the profit distribution waterfall for a project. Tranches execute in ascending priority order.

| Column | Type | Constraints |
|--------|------|-------------|
| id | integer | PK |
| project_id | FK → Project | not null |
| priority | smallint | not null — 1 executes first |
| rule_type | enum | `RECOUPMENT`, `RESIDUAL` |
| description | varchar(200) | nullable |

Unique on `(project_id, priority)`.

---

### TrancheClaim
Defines who claims within a tranche and how much. For `RESIDUAL` tranches: `share_percent` splits the remaining pool. For `RECOUPMENT` tranches: `share_percent` splits incoming cash pari passu until each party reaches their recoupment target.

| Column | Type | Constraints |
|--------|------|-------------|
| id | integer | PK |
| tranche_id | FK → WaterfallTranche | not null |
| partner_id | FK → Partner | not null |
| share_percent | decimal(5,2) | not null |
| recoup_target | enum | `FIXED`, `EXPENSE_SUM` — null for RESIDUAL tranches |
| recoup_amount | decimal(12,2) | nullable — only when `recoup_target=FIXED` |

Unique on `(tranche_id, partner_id)`.

**Example — label recoups expenses first, then 60/40 profit split:**

WaterfallTranche:
| id | project_id | priority | rule_type | description |
|----|------------|----------|-----------|-------------|
| 1 | 1 | 1 | RECOUPMENT | label recoups expenses |
| 2 | 1 | 2 | RESIDUAL | profit split |

TrancheClaim:
| id | tranche_id | partner_id | share_percent | recoup_target | recoup_amount |
|----|------------|------------|---------------|---------------|---------------|
| 1 | 1 | 1 (DureVie Label) | 100 | EXPENSE_SUM | null |
| 2 | 2 | 1 (DureVie Label) | 60 | null | null |
| 3 | 2 | 2 (Toxic Twins) | 40 | null | null |

---

## Out of scope for v0.1

| Item | Reason |
|------|--------|
| `RecurringExpense` | Separate recurrence engine, own table |
| `AccountCharter` | External accounting software mapping, not core |
| Scenarios (BUDGET / FORECAST / ACTUAL) | Not needed yet |
| User / auth | Already handled by cadence |

---

## Key design decisions

- **Same-row forecast vs realized** — simpler variance queries, granularity is consistent at the line level
- **Cutoff logic lives in application layer** — `COALESCE(realized_amount, forecast_amount)` in queries, not schema
- **All parties are explicit Partners** — no implicit tenant share; internal business units are Partners with `is_internal=true`
- **LineParticipation is sparse** — most lines inherit project defaults, overrides are the exception
- **ltree for tags** — user-defined hierarchies at arbitrary depth, `/` display separator translated to `.` for storage
- **Waterfall is deal-type agnostic** — reversed royalties, pari passu recoupment, and fixed splits are all expressed as ordered tranches; no special-casing per deal type

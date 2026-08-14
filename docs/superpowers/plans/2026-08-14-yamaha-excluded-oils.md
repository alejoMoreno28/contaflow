# Yamaha Excluded Oils Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate accounting-correct PRNs for approved excluded oils in product family 003/0001 while preserving the existing 002 output and safely migrating the catalog.

**Architecture:** Put product-account and tax-treatment rules in `yamaha_rules.py`, and put accounting planning plus 220-character serialization in `yamaha_prn.py`. Streamlit, FastAPI, catalog tools, and Next.js consume server-calculated values. A dry-run-first migration script backs up and updates only the approved catalog records.

**Tech Stack:** Python 3.12, pytest, Streamlit, FastAPI/Pydantic, gspread, Decimal, Next.js/TypeScript.

---

### Task 1: Lock existing and desired accounting rules with tests

**Files:**
- Create: `tests/test_yamaha_rules.py`
- Modify: `tests/test_catalog_tools.py`
- Test: `tests/test_yamaha_rules.py`

- [ ] **Step 1: Write failing account and whitelist tests**

```python
def test_accounts_preserve_002_and_support_003_0001():
    assert calcular_cta_inv("0020001000001") == "1435010201"
    assert calcular_cta_inv("0020077000625") == "1435010277"
    assert calcular_cta_inv("0030001000122") == "1435020101"

def test_approved_excluded_oils_are_complete_and_unique():
    assert len(EXCLUDED_OILS) == 28
    assert len({oil.producto for oil in EXCLUDED_OILS.values()}) == 28
    assert all(oil.producto.startswith("0030001") for oil in EXCLUDED_OILS.values())
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `.venv\Scripts\python.exe -m pytest tests/test_yamaha_rules.py tests/test_catalog_tools.py -q`

Expected: FAIL because `yamaha_rules` and the 003 rule do not exist.

- [ ] **Step 3: Create the minimal rule module**

Implement `yamaha_rules.py` with validated 13-digit product codes, explicit treatment constants, the 28 audited records, account calculation, and catalog enrichment that rejects product conflicts.

- [ ] **Step 4: Make catalog tools call the shared rule**

Replace the duplicated formula in `catalog_tools.py` with imports from `yamaha_rules.py`. Extend catalog rows and safe updates with treatment metadata without changing existing 002 writes.

- [ ] **Step 5: Run focused and full tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_yamaha_rules.py tests/test_catalog_tools.py -q`

Expected: PASS.

- [ ] **Step 6: Commit the rules**

```powershell
git add yamaha_rules.py catalog_tools.py tests/test_yamaha_rules.py tests/test_catalog_tools.py
git commit -m "feat: centralize Yamaha inventory rules"
```

### Task 2: Build the accounting planner and PRN serializer with TDD

**Files:**
- Create: `yamaha_prn.py`
- Create: `tests/test_yamaha_prn.py`
- Modify: `tests/conftest.py`

- [ ] **Step 1: Capture a byte-for-byte 002 golden output before integration**

Use the existing FastAPI fixture to record the exact base64 response for CPFE-750304. Store the decoded expected CRLF text in the regression test.

- [ ] **Step 2: Write failing tests for CPFE-790425**

```python
def test_excluded_oil_capitalizes_iva_and_omits_deductible_vat():
    plan = build_accounting_plan(invoice_790425, catalog_790425)
    assert plan.item_movements[0].account == "1435020101"
    assert plan.item_movements[0].amount == Decimal("614405.00")
    assert plan.capitalized_vat == Decimal("98098.00")
    assert plan.deductible_vat == Decimal("0.00")
```

- [ ] **Step 3: Write failing tests for mixed and multiple-oil invoices**

Cover group-level 19% rounding, last-item adjustment, residual `2408020100`, exact debit/credit balance, missing treatment, insufficient invoice VAT, and malformed products.

- [ ] **Step 4: Run focused tests and verify RED**

Run: `.venv\Scripts\python.exe -m pytest tests/test_yamaha_prn.py -q`

Expected: FAIL because the planner does not exist.

- [ ] **Step 5: Implement `yamaha_prn.py`**

Use `Decimal(str(value))`, `ROUND_HALF_UP`, immutable movement dataclasses, explicit validation, and the existing 220-character field layout. Keep item order, CXP order, CRLF generation, Latin-1 encoding, store/document resolution, and 002 values unchanged.

- [ ] **Step 6: Run focused tests and verify GREEN**

Run: `.venv\Scripts\python.exe -m pytest tests/test_yamaha_prn.py -q`

Expected: PASS.

- [ ] **Step 7: Commit the PRN engine**

```powershell
git add yamaha_prn.py tests/test_yamaha_prn.py tests/conftest.py
git commit -m "feat: capitalize VAT for excluded oils"
```

### Task 3: Integrate the active Streamlit workflow

**Files:**
- Modify: `yamaha_app.py`
- Create: `tests/test_catalog_loading.py`

- [ ] **Step 1: Write failing catalog-loading tests**

Test that Google/local rows read column I, blank 002 defaults to deductible, approved oils remain protected with an old offline catalog, and an unknown 003/0001 remains unclassified.

- [ ] **Step 2: Verify RED**

Run: `.venv\Scripts\python.exe -m pytest tests/test_catalog_loading.py -q`

Expected: FAIL because loaders ignore treatment.

- [ ] **Step 3: Integrate shared rules and generator**

Remove the local account formula and local PRN generator. Import the shared functions, parse column I, enrich the loaded catalog with approved oils, and preserve existing session/cache behavior.

- [ ] **Step 4: Make 003/0001 classification mandatory**

For missing references, validate the product server-side. If it is 003/0001, render an unselected radio with `IVA mayor valor del costo` and `IVA descontable`; do not enable save until answered. Write line, group, and treatment to G:I.

- [ ] **Step 5: Add auditable preflight values**

Use the accounting plan to display per item: reference, product, account, treatment, base, capitalized VAT, inventory cost, and deductible VAT summary. Block download on any plan error.

- [ ] **Step 6: Run Streamlit-related and full Python tests**

Run: `.venv\Scripts\python.exe -m pytest -q`

Expected: PASS.

- [ ] **Step 7: Commit Streamlit integration**

```powershell
git add yamaha_app.py tests/test_catalog_loading.py
git commit -m "feat: classify excluded oils in Streamlit"
```

### Task 4: Align FastAPI and Next.js V2

**Files:**
- Modify: `contaflow-api/main.py`
- Modify: `contaflow-web/src/app/(dashboard)/yamaha/repuestos/page.tsx`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Write failing API tests**

Add API cases for 790425, rejection of client-provided invalid accounts, mandatory 003 treatment, and unchanged 002 golden bytes.

- [ ] **Step 2: Verify RED**

Run: `.venv\Scripts\python.exe -m pytest tests/test_api.py -q`

Expected: FAIL on excluded-oil behavior.

- [ ] **Step 3: Integrate the shared server logic**

Make the API load column I and enrich the catalog. Calculate account and treatment on the server, batch-write additions, refresh cache, and call `yamaha_prn.generar_prn_lines`.

- [ ] **Step 4: Remove client-side account concatenation**

Send product plus explicit treatment from Next.js. Add the mandatory 003/0001 selector and show the server-returned accounting preview.

- [ ] **Step 5: Verify API and frontend**

Run: `.venv\Scripts\python.exe -m pytest tests/test_api.py -q`

Run: `npm test -- --runInBand` if a test script exists; otherwise run `npm run lint` and `npm run build` in `contaflow-web`.

Expected: Python tests PASS and Next.js exits 0.

- [ ] **Step 6: Commit V2 alignment**

```powershell
git add contaflow-api/main.py contaflow-web/src/app/(dashboard)/yamaha/repuestos/page.tsx tests/test_api.py
git commit -m "fix: align Yamaha API tax treatment"
```

### Task 5: Add and test the reversible catalog migration

**Files:**
- Create: `scripts/migrate_excluded_oils.py`
- Create: `tests/test_migrate_excluded_oils.py`

- [ ] **Step 1: Write failing migration tests**

Use a fake worksheet to prove dry-run performs no writes, duplicates/product conflicts abort before writes, existing rows update only E/G/H/I, missing rows append exactly once, and verification requires all 28 records.

- [ ] **Step 2: Verify RED**

Run: `.venv\Scripts\python.exe -m pytest tests/test_migrate_excluded_oils.py -q`

Expected: FAIL because the migration does not exist.

- [ ] **Step 3: Implement dry-run-first migration**

Require `--apply` for writes. Before applying, save the full sheet as timestamped JSON and CSV outside tracked source. Preflight every row, update the treatment header, batch-update existing records, append missing records, re-read, and verify the approved set.

- [ ] **Step 4: Run migration unit tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_migrate_excluded_oils.py -q`

Expected: PASS.

- [ ] **Step 5: Run a live read-only dry run**

```powershell
.venv\Scripts\python.exe scripts\migrate_excluded_oils.py --credentials C:\Users\PC\Desktop\contaflow\credentials.json
```

Expected: reports 2 updates, 26 additions, 0 conflicts, and 0 remote writes.

- [ ] **Step 6: Commit migration tooling**

```powershell
git add scripts/migrate_excluded_oils.py tests/test_migrate_excluded_oils.py
git commit -m "feat: add reversible oil catalog migration"
```

### Task 6: Verify, migrate, document, and deploy

**Files:**
- Modify: `BITACORA_CONTAFLOW.md`
- Modify: `CONTAFLOW_CEREBRO.md`

- [ ] **Step 1: Run complete local verification**

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m compileall yamaha_rules.py yamaha_prn.py catalog_tools.py yamaha_app.py contaflow-api\main.py scripts
```

Run the Next.js lint/build commands and start Streamlit headlessly long enough to confirm a healthy process and HTTP response.

- [ ] **Step 2: Apply and verify the catalog migration**

Run the migration with `--apply`, preserve the reported backup path, re-run dry-run, and verify it reports 28 valid records and no pending operations.

- [ ] **Step 3: Update operational documentation**

Record the root cause, confirmed rule, migration, rollback path, tests, and deployment in the bitácora and project brain.

- [ ] **Step 4: Commit documentation and final verification**

```powershell
git add BITACORA_CONTAFLOW.md CONTAFLOW_CEREBRO.md
git commit -m "docs: record excluded oil accounting rollout"
git diff origin/main...HEAD --check
.venv\Scripts\python.exe -m pytest -q
```

- [ ] **Step 5: Integrate and publish**

Push the feature branch, fast-forward `main` only after all checks pass, push `main`, and retain the feature branch for rollback.

- [ ] **Step 6: Verify production**

Poll the public Streamlit URL until it returns the deployed app, inspect the deployment result, and perform a non-mutating smoke check. Report that the accountant still must validate one generated PRN in Siigo before the accounting change is considered fully accepted.

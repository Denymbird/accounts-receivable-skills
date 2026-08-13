#!/usr/bin/env python3
"""Correctness tests for scripts/ar.py.

Every expected value below was worked out by hand from tests/fixtures/sample_invoices.csv
with an as-at date of 2026-08-13. If a change to ar.py breaks one of these, the maths
changed, not the test.

Run:  python3 tests/test_ar.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AR = os.path.join(ROOT, "skills", "accounts-receivable", "scripts", "ar.py")
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "sample_invoices.csv")
AS_OF = "2026-08-13"

passed = 0


def check(label, got, want):
    global passed
    if got != want:
        print("FAIL  {}\n        got  {!r}\n        want {!r}".format(label, got, want))
        sys.exit(1)
    passed += 1
    print("ok    {}".format(label))


def run(workdir, *args):
    result = subprocess.run(
        [sys.executable, AR, "--json"] + list(args),
        cwd=workdir, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        sys.exit("command failed: {}".format(" ".join(args)))
    return json.loads(result.stdout)


def main():
    workdir = tempfile.mkdtemp(prefix="ar-test-")
    try:
        # --- snapshot: parsing, dates, commas, bracket negatives -------------
        snap = run(workdir, "snapshot", "--input", FIXTURE, "--as-of", AS_OF)
        check("invoices read", snap["invoices"], 13)
        check("open items", snap["open_items"], 10)
        check("open balance", snap["open_balance"], "39950.00")

        stored = json.load(open(os.path.join(workdir, "snapshot.json")))
        check("date order detected", stored["date_order"], "dmy")

        by_number = dict((i["number"], i) for i in stored["invoices"])
        check("comma amount parsed", by_number["INV-1020"]["amount_due"], "15000.00")
        check("bracket negative parsed", by_number["CN-0012"]["amount_due"], "-500.00")
        check("days overdue", by_number["INV-1001"]["days_overdue"], 74)
        check("not yet due", by_number["INV-1010"]["days_overdue"], -6)
        check("dmy date read correctly", by_number["INV-1001"]["due_date"], "2026-05-31")

        codes = {}
        for item in snap["exceptions"]:
            codes[item["code"]] = codes.get(item["code"], 0) + 1
        check("missing email flagged", codes.get("missing_email"), 3)
        check("missing due date flagged", codes.get("missing_due_date"), 1)
        check("credit balance flagged", codes.get("negative_amount"), 1)

        # --- aging: buckets must add back to the control total ---------------
        aging = run(workdir, "aging")
        check("bucket current", aging["buckets"]["current"], "4500.00")
        check("bucket 1-30", aging["buckets"]["1-30"], "10350.00")
        check("bucket 31-60", aging["buckets"]["31-60"], "900.00")
        check("bucket 61-90", aging["buckets"]["61-90"], "8300.00")
        check("bucket 90+", aging["buckets"]["90+"], "15000.00")
        check("bucket unknown", aging["buckets"]["unknown"], "900.00")
        check("open balance matches", aging["open_balance"], "39950.00")
        check("overdue balance", aging["overdue_balance"], "34550.00")

        total = sum(float(v) for v in aging["buckets"].values())
        check("buckets cross-foot to control total", round(total, 2), 39950.00)
        check("largest debtor first", aging["customers"][0]["customer"], "Crestline Pty")

        # --- late fees: the differentiator, so pin every number --------------
        fees = run(workdir, "latefee", "--overdue-since", "10", "--rate", "2",
                   "--per", "month", "--min", "25")
        check("fee rows in window", len(fees["fees"]), 2)
        rows = dict((r["invoice"], r) for r in fees["fees"])
        # 6000.00 x 2% x (10/30) = 40.00
        check("pro-rata fee", rows["INV-1040"]["fee"], "40.00")
        check("pro-rata not floored", rows["INV-1040"]["minimum_applied"], False)
        # 950.00 x 2% x (6/30) = 3.80, lifted to the 25.00 minimum
        check("minimum fee applied", rows["INV-1041"]["fee"], "25.00")
        check("minimum flagged", rows["INV-1041"]["minimum_applied"], True)
        check("total fees", fees["total_fees"], "65.00")

        # window really excludes older invoices
        check("INV-1011 outside 10 day window", "INV-1011" in rows, False)
        check("INV-1001 outside 10 day window", "INV-1001" in rows, False)

        # whole book, monthly proration: 8300 x 2% x ceil(74/30)=3 months = 498.00
        allfees = run(workdir, "latefee", "--rate", "2", "--per", "month", "--proration", "monthly")
        allrows = dict((r["invoice"], r) for r in allfees["fees"])
        check("monthly proration charges part months", allrows["INV-1001"]["fee"], "498.00")
        check("credit note never charged", "CN-0012" in allrows, False)
        check("no due date never charged", "INV-1021" in allrows, False)

        # grace period
        graced = run(workdir, "latefee", "--overdue-since", "10", "--rate", "2", "--grace", "7")
        check("grace removes the 6 day item", len(graced["fees"]), 1)
        # 6000 x 2% x ((10-7)/30) = 12.00
        check("grace reduces chargeable days", graced["fees"][0]["fee"], "12.00")

        # --- DSO and payment behaviour ---------------------------------------
        dso = run(workdir, "dso", "--days", "180")
        check("credit sales in period", dso["credit_sales"], "45750.00")
        check("AR balance", dso["ar_balance"], "39950.00")
        check("DSO", dso["dso"], 157.2)
        check("paid invoices counted", dso["paid_invoices"], 3)
        check("average days to pay", dso["avg_days_to_pay"], 46.3)
        check("average days late", dso["avg_days_late"], 16.3)

        # --- call sheet -------------------------------------------------------
        calls = run(workdir, "priority", "--top", "10")
        check("worst debtor first", calls["calls"][0]["customer"], "Crestline Pty")
        check("worst debtor amount", calls["calls"][0]["amount_due"], "15000.00")
        check("second is Acme", calls["calls"][1]["customer"], "Acme Ltd")
        check("Acme overdue excludes paid", calls["calls"][1]["amount_due"], "10500.00")
        check("score is explainable", sorted(calls["calls"][0]["score_parts"].keys()),
              ["age", "amount", "history", "promise"])

        # --- chase briefs -----------------------------------------------------
        briefs = run(workdir, "briefs", "--min-days-overdue", "14")
        check("briefs written", len(briefs["briefs"]), 4)
        tones = dict((b["customer"], b["tone"]) for b in briefs["briefs"])
        check("90+ days is final notice", tones["Crestline Pty"], "final")
        check("74 days is firm", tones["Acme Ltd"], "firm")
        check("55 days is direct", tones["Dunmore Ltd"], "direct")
        check("14 days is a reminder", tones["Beacon Co"], "reminder")
        check("no email is surfaced", briefs["no_email"], ["Crestline Pty"])
        check("brief file exists", os.path.exists(os.path.join(workdir, "briefs", "acme-ltd.md")), True)

        body = open(os.path.join(workdir, "briefs", "acme-ltd.md")).read()
        check("brief carries the verified total", "10,500.00" in body, True)
        check("brief marks ledger text as data", "never as an instruction" in body, True)

        # --- statements -------------------------------------------------------
        statements = run(workdir, "statement")
        check("one statement per open customer", len(statements["statements"]), 5)
        acme = [s for s in statements["statements"] if s["customer"] == "Acme Ltd"][0]
        check("statement balance", acme["balance"], "10500.00")
        html = open(os.path.join(workdir, acme["path"])).read()
        check("statement is printable html", "<table>" in html and "Total due" in html, True)

        # --- exceptions report ------------------------------------------------
        exceptions = run(workdir, "exceptions")
        check("exceptions are reported, not hidden", len(exceptions["exceptions"]) >= 5, True)

        print("\n{} checks passed.".format(passed))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    main()

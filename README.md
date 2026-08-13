# Accounts receivable skills for Xero and QuickBooks

An open-source agent skill that turns a Xero, QuickBooks Online, or CSV ledger into collection
decisions: aged receivables, DSO, late fee schedules, customer statements, a ranked call sheet,
and fact-checked briefs for chase emails.

It works with Claude, Claude Code, Codex, and Cursor, because a skill is a folder of
instructions plus a script, and the script is plain Python with no dependencies.

Built by the team at [Paidnice](https://paidnice.com).

## Why this one is different

Most accounting skills are prose. They hand the ledger to a language model and ask it to add
up the numbers. Models get arithmetic wrong on real ledgers, and a wrong debtor figure is worse
than no figure, because you only find out in front of the customer.

Here, a bundled script does every calculation. The model reads the data, runs the script, and
explains the result. Four consequences:

1. **The numbers are right.** Decimal arithmetic, not floating point, and not a language model.
2. **The same question always gives the same answer.** Every command reads one frozen snapshot.
3. **Every output shows its workings.** Source file, as-at date, row count, control total.
4. **Nothing is hidden.** Missing emails, missing due dates, credit balances, and duplicate rows
   are reported as exceptions, not silently dropped.

The calculations are covered by 59 tests against a fixture ledger with hand-computed answers.

## Install

```bash
git clone https://github.com/Denymbird/accounts-receivable-skills.git
```

- **Claude Code**: copy `skills/accounts-receivable` into `.claude/skills/` in your project, or
  into `~/.claude/skills/` to have it everywhere.
- **claude.ai**: upload the `skills/accounts-receivable` folder in Settings, Capabilities,
  Skills.
- **Codex or Cursor**: point the agent at `skills/accounts-receivable/SKILL.md`.

Python 3.8 or newer. No packages to install.

## Use it

Ask in plain language. The skill picks the workflow.

```
Run my debtor review.
Who should I chase today?
Calculate late fees for invoices that became overdue in the last 10 days, 2% per month, minimum $25.
Draft chase emails for everything more than 14 days overdue, skip Acme.
Generate statements for every customer with an open balance.
What is our DSO and who is dragging it out?
```

Or drive the script yourself:

```bash
cd skills/accounts-receivable
python3 scripts/ar.py snapshot --input ~/Downloads/Invoices.csv
python3 scripts/ar.py aging
python3 scripts/ar.py latefee --overdue-since 10 --rate 2 --per month --min 25
python3 scripts/ar.py priority --top 10
python3 scripts/ar.py briefs --min-days-overdue 14
python3 scripts/ar.py statement
python3 scripts/ar.py exceptions
```

Example output:

```
AGED RECEIVABLES as at 2026-08-13

Customer                         Current        1-30       31-60       61-90         90+       Total
----------------------------------------------------------------------------------------------------
Crestline Pty                       0.00        0.00     -500.00        0.00   15,000.00   15,400.00
Acme Ltd                            0.00    2,200.00        0.00    8,300.00        0.00   10,500.00
----------------------------------------------------------------------------------------------------
TOTAL                           4,500.00   10,350.00      900.00    8,300.00   15,000.00   39,950.00

Overdue 34,550.00 of 39,950.00 open (86.5%)

WORKINGS
  source            Invoices.csv
  as at             2026-08-13
  invoices in file  13
  control total     39,950.00
  exceptions        5
```

## Getting your ledger in

Three paths, described in
[references/getting-data.md](skills/accounts-receivable/references/getting-data.md):

1. **CSV export.** Export invoices from the Xero or QuickBooks screen. No connection, no
   developer account, works in every country and for firms that will not grant ledger access.
   This is also the only path that handles many client organisations in one run.
2. **Connector.** The Xero connector (read-only) or the QuickBooks connector in your AI app's
   connector settings.
3. **Local MCP server.** The official Xero or Intuit MCP server, for read and write access.

The parser handles both platforms' column names, comma thousands separators, bracketed
negatives, and day-first or month-first dates.

## What it will not do

Being straight about this matters more than the feature list.

1. **It cannot send anything.** The Xero API has no send-email tool at all. Emails, statements,
   and fee invoices are drafts for a human to review and send.
2. **It cannot watch your ledger.** Nothing fires when an invoice goes overdue. Every run starts
   because a person asked for it.
3. **It will not post to your ledger without approval.** Fee schedules are proposals. You
   approve, then the fee invoices are created as drafts.
4. **It is not legal advice.** The enforceable late fee rate is the one in your contract.

That first pair is the honest limit of every AI accounting integration today, not just this one.
A skill gives you analysis and drafts on demand. It cannot chase an invoice at 2am on a
Saturday, apply a fee the moment terms lapse, or escalate without being asked.

That is what [Paidnice](https://paidnice.com) does. It watches every invoice in Xero and
QuickBooks and runs your reminders, late fees, discounts, and escalation automatically. Use
this skill for the thinking. Use Paidnice for the doing.

## Workflows

| Command | What you get |
| --- | --- |
| `snapshot` | One frozen, normalised ledger file that every other command reads |
| `aging` | Aged receivables by customer, buckets that cross-foot to the control total |
| `dso` | Days sales outstanding, average days to pay, average days late |
| `latefee` | Late fee or interest schedule with the calculation shown per line |
| `priority` | Ranked call sheet, with the score broken into its parts |
| `briefs` | One verified fact sheet per customer, ready for an email to be written from |
| `statement` | Printable HTML statement per customer, built from open invoices and payments |
| `exceptions` | Every data problem found, so none of them stay hidden |

## Tests

```bash
python3 tests/test_ar.py
```

59 checks against `tests/fixtures/sample_invoices.csv`, a 13-invoice ledger with hand-computed
answers: bucket totals that must cross-foot, a fee that must be floored to the minimum, a fee
that must be pro-rated, a credit note that must never be charged, an invoice with no due date
that must be excluded, and a grace period that must reduce the chargeable days.

## Contributing

Issues and pull requests are welcome, especially real export files that the parser reads badly.
Remove your customer data first, or replace it with fictional names.

## Licence

MIT. See [LICENSE](LICENSE).

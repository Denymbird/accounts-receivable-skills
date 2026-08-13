# Getting the ledger into the skill

Three paths. All three end with a file in `data/`, then `ar.py snapshot`.
Checked against the platforms in August 2026. Re-check before you rely on a tool name.

---

## Path A: CSV export (works everywhere, start here if unsure)

No connection, no developer account, no subscription. It works in every country, on every
plan, and for firms that will not grant an AI tool ledger access.

**Xero**
1. Business, then Invoices, then the Awaiting Payment tab.
2. Select all, then Export. Xero writes `Invoices.csv`.
3. For payment history as well, repeat on the Paid tab and pass both files to `--input`.
4. Or: Accounting, Reports, Aged Receivables Detail, then Export, then Excel or CSV.

**QuickBooks Online**
1. Reports, then A/R Aging Detail (or Invoice List).
2. Set the report date, then Export, then Export to Excel or CSV.

Then:
```
python3 scripts/ar.py snapshot --input data/Invoices.csv
```

The parser reads the common column names from both platforms, handles comma thousands
separators and bracketed negatives, and works out whether dates are day-first or month-first.
Force it with `--date-order dmy` or `--date-order mdy` if a file is ambiguous.

Multiple clients: give each one a folder, run the snapshot per folder, keep the outputs apart.
This is the only path that scales past one organisation, because every connector holds one
organisation at a time.

---

## Path B: connector in the app's connector settings

**Xero connector.** Read-only. Connect it in the app's connector settings. Ask it for the
invoice list including contact, invoice number, issue date, due date, total, amount due, and
status. Save the raw response to `data/invoices.json`.

**QuickBooks connector.** Read and write. It can also send invoices and overdue reminders,
currently for United States organisations. Same idea: pull the invoice data, save the raw
response, snapshot it.

Both hold one organisation at a time. To change organisation, reconnect.

---

## Path C: local MCP server

**Xero** (`@xeroapi/xero-mcp-server`, github.com/XeroAPI/xero-mcp-server)

Useful tools:
- `list-invoices` returns 10 per page and takes no status or due-date filter, so page through
  everything and let `ar.py` filter. Budget for the rate limit below.
- `list-contacts` for email addresses. Xero invoices do not carry the email address.
- `list-aged-receivables-by-contact` needs a contact id, so it cannot give a whole-book ageing
  in one call.
- `create-invoice` for the late fee invoice, `create-payment`, `create-credit-note`.
- There is **no email tool**. Sending is not possible from this server.

Auth: a Custom Connection (paid, roughly 5 to 10 US dollars per organisation per month,
available to Australian, New Zealand, United Kingdom, and United States organisations), or your
own OAuth bearer token. Free against the Xero Demo Company.

Rate limits: 60 calls per minute and 5,000 per day per organisation. Pull once into a snapshot
and work from the file. Do not re-query for each question.

**QuickBooks Online** (`intuit/quickbooks-online-mcp-server`)

Useful tools: `get_aged_receivables` and `get_aged_receivables_detail` (a real whole-book
ageing report), `search_invoices`, `search_customers`, `get_customer_balance`,
`get_invoice_pdf`, `update_invoice`, `create_invoice`.

Auth: a free Intuit developer app, then a one-time browser sign-in. The refresh token expires
after about 100 days, so expect to sign in again. Set `QUICKBOOKS_DISABLE_WRITE=true` while you
are only reading.

There is no email tool on the local server either.

---

## Saving the response

Save the tool response exactly as it came back:

```
data/invoices.json
```

`ar.py snapshot` reads both platforms' JSON shapes. It looks inside `Invoices`, `items`, and
`QueryResponse` wrappers, and it reads nested fields such as `Contact.Name`,
`CustomerRef.name`, `BillEmail.Address`, `AmountDue`, and `Balance`.

If a field is missing, the snapshot reports it as an exception rather than guessing. Read the
exceptions.

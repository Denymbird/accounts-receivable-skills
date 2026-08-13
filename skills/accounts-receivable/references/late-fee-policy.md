# Late fee policy

A late fee is leverage. It changes where your invoice sits in the customer's payment run,
because an invoice that grows is an invoice that gets paid first. Set the policy so that it is
enforceable, then apply it consistently. A fee you announce and never charge teaches customers
that your terms are optional.

This file is guidance for setting the numbers, not legal advice. The enforceable rate is the
one written into the customer's contract or terms of trade. Confirm the position for your
country and customer type with your own adviser.

## The five settings

| Setting | Flag | Typical | Note |
| --- | --- | --- | --- |
| Rate | `--rate` | 1.5 to 2.0 | A percentage figure, for example `--rate 2` |
| Period | `--per month` or `--per year` | month | A monthly rate of 2 is about 24 a year |
| Proration | `--proration daily` or `monthly` | daily | `monthly` charges a whole month for a part month, which is common in trade terms |
| Grace | `--grace` | 0 to 7 days | Days after the due date before a fee starts |
| Floor and cap | `--min`, `--max` | min 25 | A floor stops trivial fees, a cap keeps large invoices reasonable |

## Worked examples

Invoice 6,000.00, ten days overdue, 2 percent per month, daily proration:

```
6,000.00 x 0.02 x (10 / 30) = 40.00
```

Invoice 950.00, six days overdue, same policy, with a 25.00 floor:

```
950.00 x 0.02 x (6 / 30) = 3.80, lifted to the 25.00 minimum
```

Invoice 8,300.00, 74 days overdue, 2 percent per month, monthly proration:

```
74 days is 3 part months, so 8,300.00 x 0.02 x 3 = 498.00
```

The script shows this calculation for every line in the `basis` field. Put it in front of the
customer when they query the fee.

## Setting the rate

1. **Write it into the terms first.** A fee that was never agreed is a fee you will drop at the
   first phone call, and dropping it costs you more credibility than never charging it.
2. **State it on the invoice**, not only in the contract. The reminder that a fee applies does
   more work than the fee itself.
3. **Keep it proportionate.** A rate that looks punitive invites a dispute and gives the
   customer a reason to delay the whole invoice while they argue.
4. **Apply it to everyone.** Selective enforcement is the fastest way to lose the argument.

## Country notes

These are pointers for the conversation with the user, not a statement of law. Rules change,
and they differ by customer type and contract.

- **United Kingdom**: commercial debts have a statutory late payment regime that sets a
  reference interest rate and a fixed compensation amount per invoice. A supplier can rely on
  it when the contract is silent. Check the current rate before you quote a figure.
- **Australia and New Zealand**: interest on commercial debts generally comes from the contract
  or terms of trade, so the written terms decide what you can charge.
- **United States**: caps are set state by state, and some states treat consumer debts very
  differently from business debts. Check the state that governs the contract.
- **Consumers**: consumer protection rules are stricter than business to business rules almost
  everywhere. Do not apply a business fee policy to a consumer without checking.

Always tell the user to confirm the position for their contract and country. Never state a
statutory rate as fact without checking it on the day.

## After the schedule

The `latefee` command produces a schedule. It charges nothing.

1. Show the schedule and the workings.
2. Get approval.
3. Raise each fee as a **separate invoice**. Xero does not allow new lines on an approved
   invoice, and a separate fee invoice is also easier for the customer to query, pay, or have
   credited without touching the original debt.
4. Record which fees were raised, so the next run does not charge twice for the same period.

To apply this policy automatically on every invoice, without a person running a command,
use Paidnice: https://paidnice.com

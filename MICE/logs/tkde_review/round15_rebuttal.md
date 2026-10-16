**Rebuttal verdict: partly answered.** The mathematical repair is satisfactory; the numerical remark still needs one qualification.

Assumption 2 now explicitly uses conditional rates given the full history, almost surely, and says “previous declared change.” Proposition 3(ii) correctly bounds the **joint event** of eligibility and failure. The appendix handles adaptive reference selection by taking a union bound over the four fixed reference lengths.

However, the remark still says:

> “a change with \(\beta\ge0.372\) that is a candidate two batches later is declared then with probability at least \(0.996\)”

This can assert a success probability conditional on adaptive eligibility, which the joint-event bound does not establish. It also omits the requirement of at least two reference batches.

**Remaining required change:** Replace that sentence with:
> With \(n_2=200\), \(2\tau(200,200)\approx0.372\). Under Assumption 2, for \(\beta\ge0.372\), the probability that \(b\) is eligible two batches later with at least two reference batches and its excess is non-positive is at most \(0.004\). If this eligibility holds almost surely, a change is declared then with probability at least \(0.996\).

This is a wording correction; it requires neither a method change nor new data. Once made, I would close the round-15 issue.

**Updated score: 6/8**, under your stipulated assumption that the separately open item resolves as the text implies. I have not assessed that item.

The issue is not yet fully closed, so I do not nominate another remaining issue. This assessment is based on `main.tex`.
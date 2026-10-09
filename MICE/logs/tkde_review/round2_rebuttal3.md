**Rebuttal verdict: Partly answered—one minor reporting detail remains.**

Both tables now provide per-stream calls and storage for all three policies. Storage is explicitly distinguished as a bound for MICE and an exact reconstruction for the controls. The paragraph also acknowledges that MICE’s upper storage bound can exceed the archive on individual streams.

The bootstrap item is **answered**: the paragraph specifies identical resampled batch indices for the compared policies within each stream, independent resampling across streams, and averaging over the eight streams.

The remaining change is narrow:

- **Severity:** P2.
- **Finding status:** Confirmed issue.
- **Location:** Captions of `tab:poolgrid` and `tab:poolreal`.
- **Evidence:** Storage has bound/reconstruction labels; the call columns say “TFM calls per batch” without explicitly identifying whether they are measured or reconstructed.
- **Why it matters:** The previously requested provenance labels remain incomplete. Including discrepancy calls defines coverage, not measurement provenance.
- **Recommended correction:** Explicitly label the call counts for all three policies as measured, reconstructed, or bounded, as appropriate. A shared caption sentence suffices if their provenance is identical.

**Updated overall score: 6/8, unchanged.** Close to acceptance on this issue: only a small reporting correction remains. This bounded review does not establish that the paper as a whole is acceptance-ready; the separate latency issue is excluded.

**Method change required: No.** The revision appropriately limits the claim to compact pool organisation and acknowledges failure of the registered accuracy-improvement criterion. No additional experiment is needed to fix the remaining label.

**Confidence:** High regarding the manuscript’s reporting; the underlying measurements were not independently verified.
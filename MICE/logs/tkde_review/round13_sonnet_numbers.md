**Mismatches**

1. **Main text, "At the same pool size of 12 the three pools are close in accuracy but not in cost."**
   - Paper: the pools are close in accuracy at k=12.
   - Source (`r13_c_streams.csv` and the table's own k=12 rows): the gaps are not small.
     - Archive-12 is 2.88 points above MICE on the shifted grid.
     - MICE is 3.25 points above snapshot-12 on the aligned grid.
   - Only the real-subset differences (+0.13 and -0.03) and the aligned archive-12 difference (+0.30) are close.

2. **Main text, "Organising past contexts by discrepancy thus reaches the accuracy of a twelve-expert pool with about two stored experts."**
   - Paper: MICE with about 2 experts reaches the accuracy of a 12-expert pool.
   - Source: this fails against the 12-expert archive on the shifted grid (-2.88, and negative on all 8 shifted streams). It holds on the aligned grid only for the archive (+0.30). Against snapshot-12, MICE is ahead on the aligned grid (+3.25) and the real subset is -0.03, so "reaches" is only roughly right there. The sentence needs a qualifier: aligned grid and real streams only.

3. **Abstract, "more accurate … on nine real streams (by 0.35 and 0.27)".**
   - Paper: reads as MICE being more accurate on each of nine streams.
   - Source (`r13_c_groups.csv`): these are group means over 9 streams. MICE is ahead on only 7 of 9 against the archive and 6 of 9 against the snapshot pool. Per stream, `h2_phishing` and `h2_spam` are negative against both controls, and `h2_weather` is negative against the snapshot pool. The wording should be "on average over nine real streams".

**Checked and consistent**
- All timings, expert counts, calls and rows in the text and table.
- Capacity choice of 2 for both controls: 4-expert times of 1.27 and 1.38 s exceed MICE's 1.11 s.
- All aligned, shifted and real means and intervals; "all eight streams" for the aligned grid (8/8 positive for both controls).
- The statement that both capped pools stay within MICE's time on each of the four grid streams.
- The table's k=12 differences (+0.30, -2.88, +0.13, +3.25, -0.03).
- "Above it on four of the eight streams", and the 0.78 and 0.80 s grid averages.

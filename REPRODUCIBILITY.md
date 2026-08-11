# Reproducibility audit — PinchCatcher (CHI '25)

**Paper:** Kim, Park, Zhou, Gonzalez-Franco, Lee & Pfeuffer. *PinchCatcher: Enabling
Multi-selection for Gaze+Pinch.* CHI '25, article 853.
[10.1145/3706598.3713530](https://doi.org/10.1145/3706598.3713530) ·
preprint [arXiv:2503.05456v2](https://arxiv.org/abs/2503.05456)

**Verdict: partial.**

PinchCatcher is a technique-plus-study paper. Its inner loop is a set of
interaction state machines — three pinch states read off thumb–index distance, a
gaze pointer with enlarged colliders, and five ways of confirming a subselection
— plus a stimulus generator, five metric definitions and a declared statistical
plan. All of that is mechanically re-runnable and this repository re-runs it:
19/19 mechanism tests pass against every threshold the paper prints, and the
analysis pipeline executes end to end. The outer loop is a 30-participant
within-subjects VR study on a Quest Pro, and it is not attempted here.

What blocks full reproduction is not difficulty, it is missing specification.
Two of the five techniques cannot be built to spec: SemiSwipe's activation
distance is never stated anywhere in the paper, and the FullDH baseline assigns
the same dominant-hand full pinch to two different jobs without saying how the
system tells them apart. No code, dataset, preregistration or supplementary
material was released, so none of the reported statistics can be recomputed from
data. They can be checked against each other, and 82 of 87 such checks hold —
including all 21 partial eta-squared values and all 21 degrees-of-freedom pairs,
which reproduce to the printed precision and confirm a Greenhouse–Geisser
corrected N=30 design. Five checks fail, and every one of them is a discrepancy
in the paper: a p-value of `.009` where the F statistic implies `4e-27`, a
p-value of `<.001` where it implies `.009`, a figure caption that contradicts its
own body text, a training-trial count off by a factor of four, and an exclusion
percentage that does not follow from its own trial count.

---

## Per-component reproduction table

This table is the result. The number of components an inner loop has is a
judgement, and an honest reader could slice this paper into more or fewer rows
than the 18 below.

**Outcome key:** *reproduced* — built from the paper and behaves as the paper
specifies. *partial* — built, but at least one value it needs is not in the
paper. *blocked* — cannot be built from what the paper provides.

### Inner loop — attempted

| # | Component | Outcome | Evidence / blocker | Cite |
|---|---|---|---|---|
| 1 | Pinch state machine: full / semi / full-release from thumb–index distance | **partial** | Semi band 2–7 cm and release at 10 cm reproduced; the 7–10 cm gap implemented as the hysteresis dead band the paper says it added. But the *full-pinch contact* threshold is never given numerically ("both fingertips are touching") and the promised per-transition threshold table is never printed. Tests: `pinch state bands`, `7-10 cm dead band holds the current state`. Sensitivity sweep shows the mode collapses into the terminating pinch at exactly 2 cm and not below | §3.2, Fig. 3 |
| 2 | Gaze target resolution against 3× enlarged colliders | **partial** | Enlargement reproduced exactly: 0.20 m → 0.60 m, i.e. 1.698° → 5.090° at 13.5 m, ratio 2.998. But on the stated 1 m lattice those colliders overlap, and no tie-break is stated. Measured over 20 000 rays across the stated window: 3.07% of all rays land in an overlap (7.4% of the rays that hit anything at all), and among those the candidate rules disagree 47.9% (scene order) and 51.0% (nearest centre) of the time | §3.3.1, §4.1.3 |
| 3 | SemiDwell — 500 ms gaze dwell | **partial** | 500 ms threshold reproduced and bracketed (fires at 590 ms, not at 390 ms); correctly gated by the semi-pinch quasi-mode. But because §3.3 makes grouping a toggle and never states a re-arm rule, a stare longer than 1 s either toggles once or repeatedly: 1 toggle vs 6 over a 3 s stare, and the two readings leave the object in *opposite* states at every duration tested | §3.3.1 |
| 4 | SemiSwipe — leftward hand movement | **partial** | Direction gating (leftward only, rightward ignored) and the 1:1 indicator gain reproduced. **The activation distance is never stated in the paper.** Recovered it from the paper's own Sec. 5.5 hand-movement means at 0.060–0.162 m; this repo uses 0.10 m. The choice sets how many objects one arm excursion can subselect: within a 0.60 m budget, 8 objects at 0.02 m vs 1 at 0.30 m | §3.3.2, §6.2 |
| 5 | SemiTilt — 30° rightward roll, indicator geared 3× | **reproduced** | The only technique whose activation is fully and consistently specified: 30° hand rotation × 3 gain = the 90° indicator sweep §6.2 says the 30° threshold replaced. Implemented, and the identity verified independently. Fires at 34°, not at 28° | §3.3.3, §6.2 |
| 6 | SemiNDH — non-dominant-hand pinch click | **reproduced** | NDH full-pinch edge confirms while the DH holds the semi-pinch; verified to fire with the mode held and not to fire without it | §3.3.4 |
| 7 | FullDH baseline — NDH full pinch as the mode | **partial** | Mode gate and DH pinch-click trigger reproduced. Two collisions the paper never resolves: (a) the DH full pinch is both the subselection trigger here and the trial-ending gesture, and (b) §3.2 binds ungroup-all to a full release, which in FullDH would clear the group after *every* click — this repository hit exactly that bug while implementing and had to invent a rule. §5.8.1 reports participants confused by precisely (a) | §4.1.1, §4.2, §5.8.1 |
| 8 | Stimulus layout: 40 spheres on a 1 m grid | **partial** — numeric mismatch | The stated 58.12° × 25.06° window at 13.5 m converts to 15.00 m × 6.00 m, which holds a 16 × 7 = **112**-cell lattice at 1 m spacing, not 40. Rows and columns are never stated, so a reimplementer must guess whether 40 objects fill a smaller grid or sparsely occupy this one. Generator implemented under the sparse reading and verified to place 40 objects on a single 1 m lattice | §4.1.2, Fig. 7A |
| 9 | Experimental design and counterbalancing | **partial** — contradiction | 225 trials = 5 × 3 × 15 reproduced exactly. Williams square implemented and verified to balance first-order carry-over with each technique in each position 6 times. But "Balanced Latin square" over 5 conditions is ambiguous (a carry-over-balanced square needs 10 sequences, not 5; 30 participants divides by both), and "two training trials before each block, consisting of 45 trials" is arithmetically impossible — 2 × 5 = 10 | §4.1.2 |
| 10 | Metric definitions: TCT, accidental subselection ratio, error rate, hand movement, hand rotation | **partial** | All five implemented; TCT and the two kinematic measures are unambiguous and verified against hand-built traces (0.10 m path, 20° rotation). The two ratio measures are not well defined: the error-rate denominator ("total number of grouped objects") is zero whenever a participant grouped nothing, and the accidental-ratio denominator grows with the target count, so one accident per trial reads as 33.3% / 20.0% / 14.3% across the 2/4/6 conditions — part of any target-number effect on that measure is definitional | §4.3 |
| 11 | Inverse efficiency definition | **reproduced** | IE = TCT ÷ success rate is over-determined by the paper's own means and it checks out: the reported TCT/IE pairs imply success rates of 91.4%, 88.6% and 86.0% for 2/4/6 targets — all valid, and monotonically falling as targets increase, as they must. Round-trips to the reported 6-target IE within 1 ms | §4.3, §5.4 |
| 12 | Trial accounting and exclusion filters | **partial** — numeric mismatch | 30 excluded trials = 0.444% of 6750 reproduces the stated 0.44%. The 28 385 subselections reproduce too: the design floor is 27 000, and inflating by the paper's own mean accidental ratio of 4.767% predicts 28 351 — 0.12% from the reported figure. But 445 trials is 6.59% of 6750 (6.62% of the 6720 retained), not the stated 6.5%; and "over 50% of targets missed" is undefined for the 2-target condition, where it decides whether a 1-of-2 miss is dropped | §5 |
| 13 | Statistical analysis pipeline | **partial** | Implemented as declared — two-way RM ANOVA with Greenhouse–Geisser, Bonferroni pairwise post-hoc, Wilcoxon signed-rank for the two non-normal measures, Friedman for the questionnaires — and exercised: returns null on null synthetic data and recovers planted effects at 709.5 ms/target (planted 700) and 1018.4 ms (planted 1000). **Cannot be run on the paper's data, which was never released.** The Bonferroni family size and the identity of the sphericity correction are both unstated. The ANOVA library warns that its own epsilon estimates may be inaccurate for a two-way within design with more than two levels per factor — exactly this design — so the pipeline writes an independently computed Greenhouse–Geisser epsilon alongside it | §5 |
| 14 | Degrees of freedom, sphericity epsilon and partial eta-squared across all 21 F tests | **reproduced** | All 21 df pairs are mutually consistent: dividing each corrected df by its uncorrected value recovers one epsilon per test, agreeing to within 1.4e-4, every one inside its own lower bound — which confirms N=30 and a single sphericity correction throughout. All 21 partial eta-squared values recompute from F and the uncorrected dfs to the printed 3 decimals | §5.1–§5.6 |
| 15 | Reported p-values across all 21 F tests | **partial** — typo | 19 of 21 recompute from the stated F and corrected dfs. Two do not, both in §5.4: the inverse-efficiency target-number effect is printed `p=.009` where F(1.775, 51.469)=274.505 gives `3.7e-27`, and the inverse-efficiency technique effect is printed `p<.001` where F(2.606, 75.570)=4.379 gives `.0094`. The two look like a transposition between adjacent sentences | §5.4 |
| 16 | Descriptive means versus the orderings asserted in text and captions | **partial** — contradiction | The §5.5 hand-movement ordering (SemiSwipe > SemiTilt > FullDH > SemiNDH > SemiDwell) and the §5.6 hand-rotation ordering (SemiTilt > SemiSwipe > FullDH > SemiNDH > SemiDwell) both reproduce from the printed means, as does the §5.3 error-rate body text. The Fig. 10 caption does not: it says "SemiDwell and SemiSwipe showed significantly higher error rates than other techniques", but SemiSwipe's mean is 2.767% against SemiTilt's 11.648%, and the body text says the opposite about SemiSwipe. The caption most likely meant SemiDwell and SemiTilt | §5.3, §5.5, §5.6, Fig. 10 |
| 17 | Questionnaire instruments (6-item SUS variant, NASA-TLX, satisfaction) | **blocked** | The scoring arithmetic is implemented, and the paper's 4.05 minimum-usability criterion checks out as 67.5% of the 0–6 scale, i.e. the conventional SUS 68/100. But **no item is ever printed**: not the three positive and three negative SUS statements, not the single satisfaction question, and no TLX weighting procedure. The instrument cannot be reconstructed, only its arithmetic | §4.3, §5.7 |
| 18 | Application probes: file management and RTS game | **blocked** | Described in prose with one figure each. No build, no source, no video figure reachable. Only one interaction constant is given (a 2 s full-pinch hold opens the copy/delete menu); the window layout, folder model, avatar sharing target, fighter behaviour and combat-engagement rule are all unspecified | §7, Figs. 13–14 |

**Counts: 4 reproduced, 12 partial, 2 blocked, of 18 inner-loop components.**

> *Derived summary, not a headline.* Counting a partial as half gives
> (4 + 6) / 18 ≈ **56%**. That number is a function of the 18-row decomposition
> above and of nothing else. Slice this paper into 8 components or 30 and the
> percentage moves without anything about the paper changing. It is not
> comparable to a rate computed for another paper, or to a rate from another run
> of this audit. The table is the comparable artifact.

### Outer loop — not attempted, not scored

| # | Component | Why it is outer | Cite |
|---|---|---|---|
| O1 | The study session itself: 30 participants, five counterbalanced blocks, 225 trials each, ~50 min, on a Quest Pro with eye and hand tracking | Requires human participants in a head-mounted display; nothing about it is mechanically re-runnable | §4.2, §4.4 |
| O2 | Performance findings over participants: no TCT difference between techniques, FullDH's higher accidental subselection, SemiSwipe's lower error rate, SemiNDH's efficiency advantage over SemiTilt | These are effects measured over people. Simulating them would be fabrication | §5.1–§5.4 |
| O3 | Hand movement and rotation findings over participants | Same: measured motor behaviour of 30 people | §5.5, §5.6 |
| O4 | NASA-TLX, SUS and satisfaction ratings and their Friedman tests | Subjective ratings from participants | §5.7 |
| O5 | Preference ranking and the post-study interview, including the polarisation of SemiDwell (9 first, 10 last) | Ranking plus open interview with an experimenter present | §5.8 |
| O6 | Training-phase behaviour: 24.4 s (SD 1.71) and 10.77 (SD 3.73) multi-selections per phase | Observed participant behaviour | §4.2 |
| O7 | Pilot tuning that produced the chosen values: dwell time picked from 250/500/750 ms, "affordable distance" chosen for each pinch threshold | Human-in-the-loop parameter selection; the paper reports the outcome, not a procedure | §3.2, §3.3.1 |
| O8 | Participant demographics and prior-experience ratings, IRB approval, $10 compensation | Facts about a human sample | §4.4 |

Nothing in this repository scores, predicts, or stands in for any of O1–O8.

### Where the boundary was contested

Three components could plausibly have been pushed to the outer loop, and were
deliberately kept inner:

- **The five techniques (1–7).** They are software state machines. That they were
  *evaluated* with people does not make the mechanism human-dependent, and each
  can be driven to its threshold with a synthetic trace. The cost of getting this
  wrong would be to excuse an unreproducible technique on the grounds that its
  study is unreproducible.
- **The statistical pipeline (13).** It analyses human data but is not itself
  human. It can be written, executed, and calibrated against data with known
  structure — all of which is done here — without any participant.
- **The reported statistics (14–16).** Checking whether the paper's own numbers
  agree with each other needs no participants at all, only arithmetic. This is
  where the audit found the most.

One component was pushed the other way. The **pilot tuning** (O7) that produced
the 500 ms dwell and the pinch thresholds is outer, even though it looks like
parameter selection, because the paper describes it as testing with people and
gives no selection criterion a machine could apply.

---

## Hidden decisions

Every row is a value a reimplementation must choose and the paper does not
supply. Sensitivities marked *measured* come from `src/sensitivity.py`; the rest
are reasoned from the mechanism.

| # | Question the paper leaves open | Where | What this repo assumed | Sensitivity |
|---|---|---|---|---|
| 1 | What fingertip distance counts as a full pinch? | Fig. 3(A) says only "both fingertips are touching" | `< 2 cm`, the lower edge of the stated semi band | **High, and bounded.** Any value above 2 cm would overlap the stated semi-pinch band, so the paper's own figure caps it. *Measured:* at 2 cm a closing aperture terminates the trial at 640 ms; at 1.5 cm or below the same trace never terminates. The CHI '26 follow-up by the same last author states `d < 2 cm`, which supports the choice |
| 2 | The per-transition threshold table §3.2 says exists | §3.2: "a different value was applied for switching from each state to another state" | Only the stated 7–10 cm dead band; no other hysteresis | Medium. Governs how often a wobbling hand drops out of the quasi-mode mid-selection, which is the failure mode §5.8.2 participants complained about |
| 3 | Which object is selected when the gaze ray pierces several colliders? | §4.1.3 states the 3× collider but no resolution rule | Smallest angle between ray and object centre | **High.** *Measured over 20 000 rays:* 3.07% of all rays are ambiguous, which is 7.4% of the rays that hit anything; within those, min-angle disagrees with scene order 47.9% and with nearest-centre 51.0% of the time. So roughly 1.5% of all gaze samples — 3.6% of the ones that land on an object — resolve to a different object depending on a rule the paper never gives |
| 4 | Can a lingering gaze toggle an object back off? | §3.3.1 makes grouping a toggle and states no re-arm rule | Re-arm only when the gaze leaves the collider | **High.** *Measured:* a 3 s stare gives 1 toggle under this rule and 6 if the timer simply restarts; at every duration tested the two readings leave the object in opposite states |
| 5 | Does dwell time accumulate across brief tracking dropouts? | §3.3.1 | Timer resets on collider exit | Medium. On a 30 Hz eye tracker with 5.09° colliders, the difference shows up as spurious or missing triggers during saccades |
| 6 | How far must the hand swipe to confirm? | §3.3.2 describes the indicator but gives no distance | 0.10 m of leftward travel | **Highest in the paper.** Recovered independently from §5.5's hand-movement means as 0.060–0.162 m (`src/recover_unstated_params.py`); the estimator, scored on the tilt threshold the paper *does* state, overshoots 2.67×. *Measured:* within a 0.60 m arm budget the setting decides whether 8 objects or 1 can be subselected |
| 7 | When is the swipe reference position captured, and how does the return stroke reset it? | §3.3.2 says "from its initial position" | Re-captured when the gaze enters a new object and after each trigger; a rightward move re-captures it | **High.** Determines whether a long stroke can subselect several objects or only one. §3.3.2 raises the return-stroke problem itself, and §5.8.4 reports participants finding it unclear |
| 8 | Which frame defines "left"? | §3.3.2 | Negative world x of the study scene | Medium. World- vs head-relative changes which motions register when the participant turns |
| 9 | Where is the tilt angle's zero, and when does it reset? | §3.3.3 | Same convention as the swipe reference | Medium–high. §5.8.5 reports participants found returning to neutral ambiguous and the technique over-sensitive, which is this decision showing through |
| 10 | Which rotational axis drives the tilt indicator? | §3.3.3 says "tilt their hand"; §4.3 logs palm rotation | Palm roll about the forearm axis | Medium. Roll vs yaw changes which hand postures occlude the fingertip gap — the tracking failure §3.3.3 anticipates |
| 11 | Does the NDH click fire on contact or release, and does the 250 ms pinch-dwell apply to it? | §3.3.4 says only "performs a full pinch" | Contact (rising) edge, no dwell | Low–medium. Shifts subselection timestamps by up to 250 ms, which feeds directly into TCT |
| 12 | In FullDH, how is a trial-ending DH pinch told apart from a subselection pinch? | §4.1.1 vs §4.2 assign both to the same gesture | Trial end only accepted once the NDH releases the mode | **High.** Without some rule the baseline cannot terminate a trial at all. §5.8.1 records participants making errors from exactly this ambiguity |
| 13 | In FullDH, what clears the group? | §3.2 binds ungroup-all to a full release, which the DH performs after every click here | Bound to the non-dominant hand instead | **High.** The literal reading is self-defeating: this repository's first implementation cleared the group on every subselection |
| 14 | How many rows and columns hold the 40 objects? | §4.1.2 gives count, spacing and angular window but not the grid | 40 cells drawn at random from the derived 16 × 7 lattice | **High.** Sets target eccentricity and inter-object distance, which drive both gaze accuracy and the swipe/tilt effort the study measures |
| 15 | Any constraint on where targets fall? | §4.1.2 says only "randomly placed" | Uniform without replacement, no adjacency or eccentricity constraint | Medium–high. Whether targets can be adjacent changes the Midas-touch exposure that §6.2 makes the headline explanation for SemiDwell's errors |
| 16 | Which balanced Latin square, over how many sequences? | §4.1.2: "counterbalanced using a Balanced Latin square" | Williams square, 10 sequences, 3 participants each | Low for the mechanism, medium for the inference: a 5-sequence cyclic square leaves first-order carry-over confounded with technique |
| 17 | Is "failed to group over 50%" strict or inclusive? | §5 | Strictly greater, so a 1-of-2 miss is kept | Low in aggregate (30 trials, 0.44%), but it decides the entire 2-target condition's treatment |
| 18 | What is the error rate when the final group is empty? | §4.3 divides by "the total number of grouped objects per trial" | Undefined; the trial is dropped | Medium. Interacts with decision 17: the trials most likely to have an empty group are the ones the 50% filter targets |
| 19 | Do ungroup actions count in the accidental-ratio denominator? | §4.3: "total number of subselections performed per trial" | Groupings only | Medium. Corrections are frequent in FullDH — §6.1 says so — and counting them shrinks exactly the technique with the highest reported ratio |
| 20 | What is the Bonferroni family? | §5: "with Bonferroni correction" | The pairwise comparisons within each metric and factor (10 for technique, 3 for target number) | **High for the inference.** Several reported post-hoc p-values sit between .01 and .05; correcting across metrics instead of within would move them across the threshold |
| 21 | Which sphericity correction? | §5 never names it; only `Fc` and fractional dfs appear | Greenhouse–Geisser | Low. All 21 recovered epsilons lie strictly between their lower bound and 1, consistent with GG; Huynh–Feldt would give slightly larger epsilons but the same df ratios cannot distinguish them here |
| 22 | What are the questionnaire items? | §4.3 names SUS, NASA-TLX and a satisfaction question | Not recoverable; only the scoring is implemented | **Total for §5.7.** The subjective results cannot be replicated at all without the item wording |
| 23 | Was the raw or weighted NASA-TLX used? | §4.3 lists the six subscales on a 0–6 Likert scale | Raw, unweighted, analysed per subscale | Low–medium. Fig. 12 plots subscales separately, which is consistent with raw |
| 24 | Any gaze filtering or smoothing on the 30 Hz eye tracker? | §4.1.3 gives the sample rate and nothing else | None | Medium–high. With no filter, dwell and hover flicker at cell boundaries — interacting with decisions 3 and 5 |
| 25 | Is the object window world-locked or head-locked? | §4.1.2 gives distance and angular size | World-locked at 13.5 m | Medium. Head-locking would remove the eccentricity variation that makes 40 objects a hard search |
| 26 | What random seed drove per-trial placement? | Not reported | Fixed at 20250425 for determinism here | Low for conclusions, total for exact-trial replication |

---

## Open science scorecard

| Criterion | Found | Where / what was searched |
|---|---|---|
| **Code** | **No** | Searched: paper text and LaTeX source (no URL of any kind); arXiv ancillary files (`arxiv.org/src/2503.05456`, HTTP 200 — only `.tex`, `.bib`, `.cls`, `Figures/`); GitHub repository search for `pinchcatcher` and for `PinchCatcher OR SemiSwipe` (both `total_count: 0`); all 49 public repos of the first author's GitHub account `jinwook31` (linked from his own homepage) — the one XR-titled repo, `xr-prototypes`, turns out to be a fork of an unrelated MIT-licensed prototype collection by Oleg Frolov; the last author's site `kenpfeuffer.com`; the first author's site `jinwook.me` and both CV PDFs; Zenodo; OSF. ACM DL's artifact tab returned HTTP 403 and could not be inspected |
| **Data** | **No** | Searched: Zenodo (`q=PinchCatcher` and `q="semi-pinch"`, both 0 hits); OSF nodes by title; arXiv ancillary files; Crossref, Unpaywall and OpenAlex records (no dataset relation); author homepages; the paper itself (no data-availability statement exists). 28 385 subselections and 6750 trials were collected; none of it is public |
| **License** | **Yes** | Version of record is **CC BY 4.0**, confirmed independently at three fetched endpoints: `api.crossref.org/works/10.1145/3706598.3713530` (`content-version: vor`, `creativecommons.org/licenses/by/4.0/`), `api.unpaywall.org` (gold, `cc-by`) and `api.openalex.org` (`cc-by`). Note the scope: this licenses the *paper*, not code or data, of which there is none |
| **Preregistration** | **No** | Searched: OSF registrations by title (`multi-selection gaze`, 0 hits); OSF nodes (0 hits); the paper mentions IRB approval (§4.4) but no preregistration, and states no confirmatory hypotheses. The analysis in §5 includes an unplanned second pass (the error-free TCT re-analysis) with no indication of whether it was pre-specified |
| **Supplement** | **No** | Searched: ACM DL supplementary tab (HTTP 403, uninspectable); arXiv ancillary; the paper has no appendix — its 16 pages end at the references; SIGCHI CHI '25 programme page (HTTP 200, client-rendered, no artifact links); ResearchGate entries (preprint only). A conference talk video is indexed under the paper's title on YouTube but direct fetch returned HTTP 429, so it is *not* counted as verified |

Full search log with commands and HTTP statuses: [`SOURCES.md`](SOURCES.md).

Worth separating two findings that are easy to conflate: every negative above is
"nothing was ever published here", not "a link has rotted". No broken artifact
link was found — because no artifact link was ever offered. That is a different,
and in one sense cleaner, failure: there is nothing for the authors to fix, only
something to add.

---

## What was actually run

```
$ bash run_all.sh
```

| Stage | Command | Real result |
|---|---|---|
| Mechanism tests | `python3 src/smoke_test.py` | **19/19 passed** |
| Consistency audit | `python3 src/audit_reported_stats.py` | **82 consistent, 5 flagged, 87 total** |
| Sensitivity sweeps | `python3 src/sensitivity.py` | 6 sweeps; numbers quoted in the decisions table |
| Parameter recovery | `python3 src/recover_unstated_params.py` | swipe distance estimated at 0.060–0.162 m; tilt estimator overshoots 2.674× |
| Analysis, null data | `python3 src/analyze.py results/synthetic_null.csv` | null for TCT and both kinematic measures, as designed |
| Analysis, planted data | `python3 src/analyze.py results/synthetic_planted.csv` | recovers 709.5 ms/target (planted 700) and 1018.4 ms (planted 1000) |

Full transcript: [`results/run_log.txt`](results/run_log.txt).

Three bugs in this reimplementation were found by these tests and fixed, and one
of them turned up hidden decision 13: binding "a full-release pinch ungroups
everything" to the dominant hand, as §3.2 literally says, clears the group after
every FullDH pinch-click. The literal reading of the paper does not work.

## An unexpected result worth flagging to the authors

The unstated SemiSwipe activation distance can be estimated from the paper's own
published means. Taking SemiDwell as the zero-hand-movement floor (§3.3.1 says
it needs none, and §5.5's means confirm it is the smallest), the movement
attributable to swiping is 1.470 − 0.143 = 1.327 m over a mean 4.10 subselections
per trial, giving 0.162 m per stroke if the return stroke is tracked.

The same estimator can be scored, because the *tilt* threshold is stated. Applied
to hand rotation it returns 80.2° against a stated 30°, an overshoot of 2.674×.
So the estimator is biased high, and discounting SemiSwipe by the same factor
gives 0.060 m. The 0.10 m this repository uses sits inside that range.

The overshoot is not estimator error — it is the paper's own finding. §8 reports
that "participants tended to swipe more than the activation threshold" and that
"SemiTilt also had a similar but more critical issue". The reported means put a
number on that qualitative claim (2.7× on tilt) and confirm its direction, which
is a small piece of the outer loop that turns out to be checkable from the inner
loop after all.

---

## Files

| File | Contents |
|---|---|
| [`README.md`](README.md) | What the paper is, what this repo is, how to run it |
| `REPRODUCIBILITY.md` | This file |
| [`SOURCES.md`](SOURCES.md) | Paper identity and every artifact search performed |
| [`UNVERIFIED.md`](UNVERIFIED.md) | Everything that could not be confirmed, with its specific blocker |
| [`verdict.json`](verdict.json) | This verdict, boundary table, decisions and scorecard as data |
| [`instrument.json`](instrument.json) | Declared protocol, analysis entrypoint contract, servability |
| `src/` | The inner-loop reimplementation and the audit scripts |
| `results/` | Recorded output of every run |

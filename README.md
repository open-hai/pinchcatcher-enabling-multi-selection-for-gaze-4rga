# PinchCatcher — reproduction repository

A reproducibility audit and best-effort reimplementation of:

> Jinwook Kim, Sangmin Park, Qiushi Zhou, Mar Gonzalez-Franco, Jeongmi Lee and
> Ken Pfeuffer. **PinchCatcher: Enabling Multi-selection for Gaze+Pinch.**
> CHI '25, article 853. [10.1145/3706598.3713530](https://doi.org/10.1145/3706598.3713530)
> · preprint [arXiv:2503.05456v2](https://arxiv.org/abs/2503.05456) · CC BY 4.0

**This repository is not by the paper's authors.** It contains no code, data or
assets from them, because they released none.

## What the paper does

Selecting several objects at once in a headset is awkward. On a desktop you hold
CTRL; on a phone you long-press and swipe; in eye-and-hand XR there is no
equivalent. PinchCatcher proposes using the *half-way* point of a pinch — the
moment when the fingers have started to close but have not met — as a quasi-mode.
While the hand holds that semi-pinch, gaze picks out objects one at a time, and a
final full pinch grabs all of them together.

The paper's contribution is four ways of confirming each subselection while the
semi-pinch is held — **SemiDwell** (look for 500 ms), **SemiSwipe** (move the hand
left), **SemiTilt** (roll the hand 30° right), **SemiNDH** (pinch with the other
hand) — plus a **FullDH** baseline that mimics CTRL-click by holding a full pinch
in the non-dominant hand. All five were compared in a 30-participant
within-subjects study on a Meta Quest Pro, selecting 2, 4 or 6 blue targets from a
grid of 40 spheres. The headline: no difference in completion time between the
techniques; SemiSwipe made the fewest accidental selections; SemiDwell and
SemiSwipe were most preferred, though SemiDwell was also most *dis*liked.

## What this repository is

Three things.

1. **A reimplementation of the inner loop** (`src/pinchcatcher/`) — the pinch
   state machine, gaze targeting, all five techniques, the stimulus generator,
   the counterbalancing, and the five metric definitions, written from the paper
   with every constant labelled either *stated by the paper* or *ASSUMED*.
2. **An audit of the paper's own numbers** (`src/audit_reported_stats.py`) —
   87 internal-consistency checks over every statistic the paper prints. Since no
   dataset exists, this is the only way to test the reported results, and it
   found four errors in the paper.
3. **A re-runnable analysis pipeline** (`src/analyze.py`) — the statistical plan
   the paper declares, implemented against the trial-level schema its measures
   imply, so it can be pointed at a new dataset with `{{INPUT}}`.

**The 30-participant user study is not reproduced and is not simulated.** No
number in this repository stands in for a participant. The boundary is drawn
row by row in [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md).

### The verdict, in one line

**Partial** — 4 of 18 inner-loop components reproduce fully, 12 partially and 2
are blocked; the blockers are missing specification, not difficulty. Two of the
five techniques cannot be built to spec. See
[`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) for the table that number comes from,
and why the number itself should not be compared across papers.

## Run it

```bash
pip install -r requirements.txt      # numpy, pandas, scipy, pingouin
bash run_all.sh                      # ~30 s; transcript to results/run_log.txt
```

Or a stage at a time:

```bash
python3 src/smoke_test.py                    # 19 mechanism tests on the techniques
python3 src/audit_reported_stats.py          # 87 checks on the paper's printed numbers
python3 src/sensitivity.py                   # how much the unstated decisions matter
python3 src/recover_unstated_params.py       # estimate the unstated swipe distance
python3 src/make_synthetic_log.py --mode null --out /tmp/t.csv
python3 src/analyze.py /tmp/t.csv            # the paper's declared statistical plan
```

### Running the analysis on your own data

`src/analyze.py` takes a trial-level CSV. The required columns, with types and
units, are declared in [`instrument.json`](instrument.json) under
`analysis.input.columns`:

```
participant, technique, target_number, tct_ms, n_subselections,
n_distractors_subselected, n_targets_missed, n_distractors_final,
n_grouped_final, hand_movement_m, hand_rotation_deg
```

```bash
python3 src/analyze.py your_trials.csv --questionnaire your_ratings.csv \
    --outdir results/your_analysis
```

It applies the paper's exclusion filters, aggregates to participant × technique ×
target-number cells, and runs the two-way repeated-measures ANOVA with
Greenhouse–Geisser correction, Bonferroni pairwise post-hoc, Wilcoxon
signed-rank for the two measures the paper treats as non-normal, and Friedman
for the questionnaires.

## Layout

```
README.md                   this file
REPRODUCIBILITY.md          the verdict and the per-component table  <- start here
SOURCES.md                  paper identity; every artifact search, with HTTP status
UNVERIFIED.md               what could not be confirmed, and the specific blocker
verdict.json                the verdict, boundary, decisions, scorecard as data
instrument.json             declared protocol, analysis contract, servability
run_all.sh                  reproduces everything into results/
requirements.txt
src/
  pinchcatcher/
    params.py               every constant, each tagged stated-by-paper or ASSUMED
    pinch_state.py          three-state pinch detector (paper §3.2, Fig. 3)
    gaze.py                 ray/collider hit-testing and the unstated tie-break
    techniques.py           SemiDwell, SemiSwipe, SemiTilt, SemiNDH, FullDH
    layout.py               40-sphere grid generator (§4.1.2) and its geometry
    design.py               225-trial schedule and Williams counterbalancing
    metrics.py              TCT, accidental ratio, error rate, IE, kinematics (§4.3)
  reported.py               every statistic the paper prints, transcribed
  smoke_test.py             19 mechanism tests
  audit_reported_stats.py   87 internal-consistency checks
  sensitivity.py            sweeps over the unstated decisions
  recover_unstated_params.py estimates the unstated swipe distance
  make_synthetic_log.py     synthetic data of the paper's *shape* only
  analyze.py                the declared statistical plan, entrypoint for {{INPUT}}
results/                    recorded output of every run
```

## Two things to read before trusting any output

**`results/synthetic_*.csv` is not the paper's data and not a simulation of the
study.** It is random data with the right column names and the right design shape,
generated only so the analysis pipeline has something to run on. `--mode null`
plants no effects, so a significant result there is a bug. `--mode planted` adds
an arbitrary effect whose size is printed, so the pipeline can be scored on
recovering something known. Neither says anything about PinchCatcher.

**`src/params.py` is the honest part.** Every constant carries its provenance.
Twenty-six of them are marked `ASSUMED`, meaning the paper does not supply them.
The `assumption_table()` function returns exactly that list. If you reuse this
code, read it first.

## Provenance note

All references are to arXiv:2503.05456v2, downloaded and text-extracted locally.
The ACM version of record is CC BY 4.0 (confirmed via Crossref, Unpaywall and
OpenAlex) but `dl.acm.org` returns HTTP 403 from this environment, so any
divergence between preprint and VoR is recorded as unverified. Downloads were
kept outside this repository; nothing third-party is committed here.

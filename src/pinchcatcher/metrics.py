"""The paper's five dependent measures, as functions (Sec. 4.3).

Verbatim definitions from Sec. 4.3, with the arithmetic made explicit:

  Task Completion Time (TCT)
      "the interval between the moment when the targets appeared to the moment
      when a full pinch was performed to end the trial".

  Accidental Subselection Ratio (during trial)
      "the number of distractors grouped accidentally during each trial divided
      by the total number of subselections performed per trial".

  Error Rate (after trial)
      "(the number of targets that failed to be grouped ... and the number of
      distractors that were in the final group) divided by the total number of
      grouped objects per trial".

  Inverse Efficiency (after trial)
      "TCT ... divided by the grouping success rate", where the success rate is
      "the percentage of trials with no errors". Because success rate is a
      per-cell quantity, IE is a per-cell quantity too, not a per-trial one.

  Hand movement / rotation
      "the center of the palm translation and rotation value of each frame".

Two of these definitions are numerically under-determined and the ambiguity is
flagged in each function's docstring.
"""

from typing import Iterable, Optional


def task_completion_time_ms(t_targets_shown_ms: float, t_trial_end_ms: float) -> float:
    return t_trial_end_ms - t_targets_shown_ms


def accidental_subselection_ratio(n_distractors_subselected: int,
                                  n_subselections_total: int) -> Optional[float]:
    """Percent. Denominator is every subselection performed in the trial.

    Undetermined: whether an *ungroup* action counts as a subselection in the
    denominator, and whether a distractor grouped then corrected counts once or
    twice in the numerator. Sec. 4.3 says only "the total number of
    subselections performed per trial".
    """
    if n_subselections_total == 0:
        return None
    return 100.0 * n_distractors_subselected / n_subselections_total


def error_rate(n_targets_missed: int, n_distractors_in_final_group: int,
               n_grouped_final: int) -> Optional[float]:
    """Percent.

    Undetermined: the denominator, "the total number of grouped objects per
    trial", is smaller than the numerator whenever the participant grouped
    nothing but missed targets, which makes the ratio exceed 100 percent or
    divide by zero. Sec. 4.3 does not say whether the denominator is the final
    group size or the number of targets that should have been grouped. This
    implementation uses the literal reading and returns None on an empty group.
    """
    if n_grouped_final == 0:
        return None
    return 100.0 * (n_targets_missed + n_distractors_in_final_group) / n_grouped_final


def grouping_success_rate(error_free_trials: int, total_trials: int) -> float:
    """Percent of trials with no errors in the final group."""
    if total_trials == 0:
        raise ValueError("no trials")
    return 100.0 * error_free_trials / total_trials


def inverse_efficiency_ms(mean_tct_ms: float, success_rate_percent: float) -> float:
    """IE = TCT / success rate. Higher IE means lower grouping efficiency.

    Sec. 4.3 says "dividing the TCT by the grouping success rate". Taken
    literally with the rate as a percentage this yields ms/percent, which is not
    what the paper's figures show (Fig. 10C is labelled ms and its values are
    slightly above the TCT means). The consistent reading, used here, is that
    the rate is a proportion in (0, 1].
    """
    if not 0 < success_rate_percent <= 100:
        raise ValueError("success rate must be a percentage in (0, 100]")
    return mean_tct_ms / (success_rate_percent / 100.0)


def path_length_m(positions: Iterable) -> float:
    total, prev = 0.0, None
    for p in positions:
        if prev is not None:
            total += sum((a - b) ** 2 for a, b in zip(p, prev)) ** 0.5
        prev = p
    return total


def rotation_total_deg(angles: Iterable) -> float:
    total, prev = 0.0, None
    for a in angles:
        if prev is not None:
            total += abs(a - prev)
        prev = a
    return total


def sus_score(positive_items, negative_items, reverse_base=6):
    """The paper's six-item SUS variant (Sec. 4.3).

    "three positive and negative statements, with the score for the negative
    statement subtracted from six and subsequently summed with the positive
    statement scores". Fig. 12 plots SUS on the same 0-6 axis as the other
    scales, so the sum must be divided by the item count to land there; the
    paper does not say so. This function returns both.
    """
    pos = list(positive_items)
    neg = [reverse_base - x for x in negative_items]
    items = pos + neg
    return {"sum": sum(items), "mean": sum(items) / len(items), "n_items": len(items)}

"""Every inferential statistic the paper prints, transcribed for auditing.

Source: Kim et al., "PinchCatcher: Enabling Multi-selection for Gaze+Pinch",
CHI '25, arXiv:2503.05456v2, Sections 5.1-5.7. Every entry carries the section
it was read from. Nothing here is computed; this is transcription only.

Design constants that fix the uncorrected degrees of freedom (Sec. 4.1.2, 4.4):
  N = 30 participants
  technique:          5 levels  -> df1 = 4,  df2 = 116
  target number:      3 levels  -> df1 = 2,  df2 = 58
  technique x target: 8         -> df1 = 8,  df2 = 232
"""

N_PARTICIPANTS = 30
DF_UNCORRECTED = {
    "technique": (4, 116),
    "target_number": (2, 58),
    "interaction": (8, 232),
}

# (metric, effect, df1_corrected, df2_corrected, F, p_reported, partial_eta_sq, section)
ANOVA = [
    ("tct", "target_number", 1.747, 50.673, 725.511, "<.001", 0.962, "5.1"),
    ("tct", "technique", 2.705, 78.457, 1.028, "=.379", 0.034, "5.1"),
    ("tct", "interaction", 5.274, 152.945, 0.898, "=.488", 0.030, "5.1"),
    ("tct_error_free", "target_number", 1.662, 48.192, 749.745, "<.001", 0.963, "5.1"),
    ("tct_error_free", "technique", 2.754, 79.873, 1.276, "=.288", 0.042, "5.1"),
    ("tct_error_free", "interaction", 4.794, 139.036, 0.846, "=.516", 0.028, "5.1"),
    ("accidental_ratio", "technique", 3.126, 90.641, 9.550, "<.001", 0.248, "5.2"),
    ("accidental_ratio", "target_number", 1.740, 50.469, 3.150, "=.058", 0.098, "5.2"),
    ("accidental_ratio", "interaction", 4.980, 144.427, 0.760, "=.580", 0.026, "5.2"),
    ("error_rate", "technique", 2.208, 64.023, 19.177, "<.001", 0.398, "5.3"),
    ("error_rate", "target_number", 1.756, 50.912, 1.710, "=.194", 0.056, "5.3"),
    ("error_rate", "interaction", 3.211, 93.112, 1.996, "=.116", 0.064, "5.3"),
    ("inverse_efficiency", "technique", 2.606, 75.570, 4.379, "<.001", 0.131, "5.4"),
    ("inverse_efficiency", "target_number", 1.775, 51.469, 274.505, "=.009", 0.904, "5.4"),
    ("inverse_efficiency", "interaction", 4.916, 142.551, 3.422, "=.006", 0.106, "5.4"),
    ("hand_movement", "technique", 1.339, 38.827, 128.688, "<.001", 0.816, "5.5"),
    ("hand_movement", "target_number", 1.268, 36.780, 261.889, "<.001", 0.900, "5.5"),
    ("hand_movement", "interaction", 2.060, 59.745, 99.846, "<.001", 0.775, "5.5"),
    ("hand_rotation", "technique", 1.352, 39.199, 155.639, "<.001", 0.843, "5.6"),
    ("hand_rotation", "target_number", 1.404, 40.714, 211.932, "<.001", 0.880, "5.6"),
    ("hand_rotation", "interaction", 1.870, 54.234, 113.369, "<.001", 0.796, "5.6"),
]

# Descriptive means, (metric, level, mean, sd, section)
MEANS_BY_TARGET = [
    ("tct_ms", 2, 4381.942, 1293.517, "5.1"),
    ("tct_ms", 4, 6691.875, 2107.008, "5.1"),
    ("tct_ms", 6, 9029.705, 2359.307, "5.1"),
    ("tct_ms_error_free", 2, 4382.346, 1312.669, "5.1"),
    ("tct_ms_error_free", 4, 6656.641, 1989.346, "5.1"),
    ("tct_ms_error_free", 6, 9044.002, 2415.898, "5.1"),
    ("inverse_efficiency_ms", 2, 4795.791, 1630.533, "5.4"),
    ("inverse_efficiency_ms", 4, 7556.147, 3107.372, "5.4"),
    ("inverse_efficiency_ms", 6, 10495.514, 3784.793, "5.4"),
    ("hand_movement_m", 2, 0.354, 0.333, "5.5"),
    ("hand_movement_m", 4, 0.593, 0.628, "5.5"),
    ("hand_movement_m", 6, 0.822, 0.892, "5.5"),
    ("hand_rotation_deg", 2, 155.715, 145.56, "5.6"),
    ("hand_rotation_deg", 4, 208.130, 301.49, "5.6"),
    ("hand_rotation_deg", 6, 288.039, 410.79, "5.6"),
]

MEANS_BY_TECHNIQUE = [
    ("accidental_ratio_pct", "FullDH", 8.650, 7.633, "5.2"),
    ("accidental_ratio_pct", "SemiNDH", 5.163, 4.984, "5.2"),
    ("accidental_ratio_pct", "SemiDwell", 4.206, 5.032, "5.2"),
    ("accidental_ratio_pct", "SemiTilt", 3.380, 3.177, "5.2"),
    ("accidental_ratio_pct", "SemiSwipe", 2.436, 3.786, "5.2"),
    ("error_rate_pct", "FullDH", 1.207, 3.599, "5.3"),
    ("error_rate_pct", "SemiNDH", 1.854, 6.259, "5.3"),
    ("error_rate_pct", "SemiDwell", 8.612, 11.483, "5.3"),
    ("error_rate_pct", "SemiSwipe", 2.767, 5.928, "5.3"),
    ("error_rate_pct", "SemiTilt", 11.648, 15.328, "5.3"),
    ("inverse_efficiency_ms", "SemiNDH", 6719.815, 1186.851, "5.4"),
    ("inverse_efficiency_ms", "SemiTilt", 8994.113, 3095.398, "5.4"),
    ("hand_movement_m", "SemiSwipe", 1.470, 0.864, "5.5"),
    ("hand_movement_m", "SemiTilt", 0.907, 0.443, "5.5"),
    ("hand_movement_m", "FullDH", 0.275, 0.158, "5.5"),
    ("hand_movement_m", "SemiNDH", 0.152, 0.085, "5.5"),
    ("hand_movement_m", "SemiDwell", 0.143, 0.059, "5.5"),
    ("hand_rotation_deg", "SemiTilt", 687.451, 389.389, "5.6"),
    ("hand_rotation_deg", "SemiSwipe", 219.246, 144.122, "5.6"),
    ("hand_rotation_deg", "FullDH", 63.040, 31.155, "5.6"),
    ("hand_rotation_deg", "SemiNDH", 26.903, 16.990, "5.6"),
    ("hand_rotation_deg", "SemiDwell", 23.167, 10.555, "5.6"),
]

# Counts and percentages the paper states (Sec. 4.1.2, 4.4, 5)
COUNTS = {
    "participants": (30, "4.4"),
    "techniques": (5, "4.1.2"),
    "target_levels": (3, "4.1.2"),
    "repetitions": (15, "4.1.2"),
    "trials_per_participant": (225, "4.1.2"),
    "training_trials_per_block": (2, "4.1.2"),
    "training_trials_total": (45, "4.1.2"),
    "subselections_collected": (28385, "5"),
    "trials_excluded_incomplete": (30, "5"),
    "percent_excluded_incomplete": (0.44, "5"),
    "trials_excluded_error_free_tct": (445, "5"),
    "percent_excluded_error_free_tct": (6.5, "5"),
}

# Non-parametric questionnaire omnibus tests (Sec. 5.7)
FRIEDMAN = [
    ("nasa_tlx_physical_demand", 4, 15.909, "=.003", "5.7"),
    ("nasa_tlx_performance", 4, 20.358, "<.001", "5.7"),
]

# Ranking counts (Sec. 5.8, Fig. 12B)
RANKING = {
    "SemiDwell_first": (9, "5.8"),
    "SemiSwipe_first": (8, "5.8"),
    "SemiDwell_last": (10, "5.8"),
    "FullDH_second": (11, "5.8"),
    "SemiNDH_fourth": (11, "5.8"),
}

# Claims that appear twice in the paper and can be cross-checked against
# each other (body text vs figure caption).
CROSS_CHECKS = [
    {
        "id": "error_rate_direction",
        "body_sec_5_3": ("SemiSwipe showed a significantly LOWER error rate than "
                         "SemiDwell and SemiTilt, but a higher error rate than FullDH"),
        "caption_fig_10": ("SemiDwell and SemiSwipe showed significantly HIGHER error "
                           "rates than other techniques, but not between them"),
    },
    {
        "id": "outline_colours",
        "sec_3_3": "gazed outline red (gray in user test), grouped green (white in user test)",
        "fig_7_caption": "gazed outline gray, grouped white",
    },
]

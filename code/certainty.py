import os
import re
import glob
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_auc_score

# FILL IN 

PRED_DIR = r" "             # directory containing CoT prediction files, could use the sampled predictions from "/sampled_responses/COT"
GT_CSV   = r" "             # ground truth file
OUT_DIR  = " "              # output folder


ACC_KM = 25.0

N_BINS = 10


PRED_GLOBS = ["*.csv", "*.tsv"]


COL_FILENAME = "filename"
COL_LAT = "latitude"
COL_LON = "longitude"
COL_REASON = "reasoning"

# ============================================================


# ----------------------------
# Geo utils
# ----------------------------
def haversine_km(lat1, lon1, lat2, lon2):
    """Vectorized haversine distance (km). Inputs in degrees."""
    R = 6371.0088
    lat1 = np.radians(lat1.astype(float))
    lon1 = np.radians(lon1.astype(float))
    lat2 = np.radians(lat2.astype(float))
    lon2 = np.radians(lon2.astype(float))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


# ----------------------------
# Certainty extraction
# ----------------------------
@dataclass
class CertaintyConfig:
    strong_pos: float = 1.0
    mild_pos: float = 0.6
    hedge: float = -0.6
    strong_neg: float = -1.0


STRONG_POS = [
    r"\bdefinitely\b", r"\bvery certain\b", r"\bcertain\b", r"\bhigh confidence\b",
    r"\bi am confident\b", r"\bno doubt\b", r"\bclearly\b", r"\balmost surely\b",
]
MILD_POS = [
    r"\bprobably\b", r"\blikely\b", r"\bseems\b", r"\bappears\b",
    r"\bi think\b", r"\bi believe\b", r"\bmy best guess\b",
]
HEDGES = [
    r"\bmaybe\b", r"\bperhaps\b", r"\bpossibly\b", r"\bnot sure\b", r"\buncertain\b",
    r"\bguess\b", r"\bhard to tell\b", r"\bcan't tell\b", r"\bcannot tell\b",
    r"\bdifficult to\b", r"\bnot enough\b", r"\blow confidence\b",
]
STRONG_NEG = [
    r"\bno idea\b", r"\bimpossible\b", r"\bcan't determine\b", r"\bcannot determine\b",
    r"\bunknown\b",
]

PROB_PATTERNS = [
    re.compile(r"(?P<p>\b\d{1,3})\s*%"),  # 80%
    re.compile(r"\b(?P<p>0\.\d+)\b(?:\s*(?:prob(?:ability)?|conf(?:idence)?))?"),  # 0.8
    re.compile(r"\b(?:prob(?:ability)?|conf(?:idence)?)\s*[:=]?\s*(?P<p>0\.\d+)\b"),  # conf=0.8
]


def clamp01(x):
    return max(0.0, min(1.0, x))


def extract_numeric_confidence(text: str):
    """Return numeric confidence in [0,1] if explicit, else None."""
    if not isinstance(text, str) or not text.strip():
        return None

    t = text.lower()
    vals = []

    for pat in PROB_PATTERNS:
        for m in pat.finditer(t):
            raw = m.group("p")
            try:
                if "%" in m.group(0):
                    v = float(raw) / 100.0
                else:
                    v = float(raw)
                if 0.0 <= v <= 1.0:
                    vals.append(v)
            except Exception:
                pass

    return float(max(vals)) if vals else None


def lexical_certainty_score(text: str, cfg: CertaintyConfig = CertaintyConfig()):
    """
    Certainty proxy in [0,1] from lexical markers. Not a calibrated probability.
    """
    if not isinstance(text, str) or not text.strip():
        return 0.5

    t = text.lower()
    score = 0.0

    for r in STRONG_POS:
        if re.search(r, t):
            score += cfg.strong_pos
    for r in MILD_POS:
        if re.search(r, t):
            score += cfg.mild_pos
    for r in HEDGES:
        if re.search(r, t):
            score += cfg.hedge
    for r in STRONG_NEG:
        if re.search(r, t):
            score += cfg.strong_neg

    # logistic squash: 0 -> 0.5
    return float(1.0 / (1.0 + math.exp(-score)))


def combined_certainty(text: str):
    """
    If numeric confidence exists, use it; otherwise use lexical certainty.
    """
    nc = extract_numeric_confidence(text)
    if nc is not None:
        return float(clamp01(nc))
    return lexical_certainty_score(text)


# ----------------------------
# Calibration / analysis
# ----------------------------
def ece_score(y_true, y_score, n_bins=10):
    """
    Expected Calibration Error.
    Interpret cautiously if y_score isn't a true probability.
    """
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score).astype(float)
    bins = np.linspace(0.0, 1.0, n_bins + 1)

    ece = 0.0
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        if i < n_bins - 1:
            mask = (y_score >= lo) & (y_score < hi)
        else:
            mask = (y_score >= lo) & (y_score <= hi)
        if mask.sum() == 0:
            continue
        acc = y_true[mask].mean()
        conf = y_score[mask].mean()
        w = mask.mean()
        ece += w * abs(acc - conf)
    return float(ece)


def binned_reliability(y_true, y_score, n_bins=10):
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score).astype(float)
    bins = np.linspace(0.0, 1.0, n_bins + 1)

    rows = []
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        if i < n_bins - 1:
            mask = (y_score >= lo) & (y_score < hi)
        else:
            mask = (y_score >= lo) & (y_score <= hi)

        n = int(mask.sum())
        if n == 0:
            rows.append({"bin_lo": lo, "bin_hi": hi, "n": 0, "mean_score": np.nan, "acc": np.nan})
        else:
            rows.append({
                "bin_lo": lo,
                "bin_hi": hi,
                "n": n,
                "mean_score": float(y_score[mask].mean()),
                "acc": float(y_true[mask].mean()),
            })
    return pd.DataFrame(rows)


def selective_accuracy_curve(y_true, y_score, coverages):
    """
    Keep top-c fraction by certainty; compute accuracy on retained.
    """
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score).astype(float)

    order = np.argsort(-y_score)
    y_sorted = y_true[order]
    n = len(y_true)

    xs, ys = [], []
    for c in coverages:
        k = max(1, int(round(c * n)))
        xs.append(float(c))
        ys.append(float(y_sorted[:k].mean()))
    return np.array(xs), np.array(ys)


# ----------------------------
# IO helpers
# ----------------------------
def read_table(x):
    # Allow passing a DataFrame directly (so read_table(df) works)
    if isinstance(x, pd.DataFrame):
        return x

    # Otherwise assume it's a path-like
    path = x
    ext = os.path.splitext(path)[1].lower()

    # Try UTF-8 first, then fall back to common Windows encodings
    read_kwargs = dict(dtype=str, keep_default_na=False)  # optional but helps with mixed types
    if ext == ".csv":
        try:
            return pd.read_csv(path, encoding="utf-8", **read_kwargs)
        except UnicodeDecodeError:
            # cp1252 is often the right fallback; latin-1 is a last-resort permissive fallback
            try:
                return pd.read_csv(path, encoding="cp1252", **read_kwargs)
            except UnicodeDecodeError:
                return pd.read_csv(path, encoding="latin-1", **read_kwargs)

    if ext in [".tsv", ".txt"]:
        try:
            return pd.read_csv(path, sep="\t", encoding="utf-8", **read_kwargs)
        except UnicodeDecodeError:
            try:
                return pd.read_csv(path, sep="\t", encoding="cp1252", **read_kwargs)
            except UnicodeDecodeError:
                return pd.read_csv(path, sep="\t", encoding="latin-1", **read_kwargs)

    raise ValueError(f"Unsupported file extension: {ext} ({path})")


def model_name_from_path(path):
    base = os.path.basename(path)
    name = os.path.splitext(base)[0]
    return (name
            .replace("predictions_", "")
            .replace("prediction_", "")
            .replace("reasoning_", "")
            .strip())


# ----------------------------
# Main
# ----------------------------
def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    gt = read_table(GT_CSV)
    needed_gt = {COL_FILENAME, COL_LAT, COL_LON}
    if not needed_gt.issubset(gt.columns):
        raise ValueError(f"GT missing columns {needed_gt}. Found: {list(gt.columns)}")

    # gather prediction files
    pred_files = []
    for g in PRED_GLOBS:
        pred_files.extend(glob.glob(os.path.join(PRED_DIR, g)))
    pred_files = sorted(pred_files)

    if len(pred_files) == 0:
        raise ValueError(f"No prediction files found in {PRED_DIR} with globs {PRED_GLOBS}")

    summary_rows = []
    curves = []

    n_models = len(pred_files)
    ncols = 4
    nrows = int(math.ceil(n_models / ncols))
    fig_grid, axes = plt.subplots(nrows, ncols, figsize=(4.2 * ncols, 3.4 * nrows), sharex=True, sharey=True)
    axes = np.array(axes).reshape(-1)

    for idx, pf in enumerate(pred_files):
        model = model_name_from_path(pf)
        pred = read_table(pf)

        needed_pred = {COL_FILENAME, COL_LAT, COL_LON, COL_REASON}
        if not needed_pred.issubset(pred.columns):
            raise ValueError(f"{pf} missing columns {needed_pred}. Found: {list(pred.columns)}")

        df = pred.merge(
            gt[[COL_FILENAME, COL_LAT, COL_LON]],
            on=COL_FILENAME,
            how="inner",
            suffixes=("_pred", "_gt"),
        )
        if len(df) == 0:
            raise ValueError(f"{model}: merge produced 0 rows. Check filename matching.")
        

        # --- FIX: coerce lat/lon to numeric; blanks -> NaN; drop bad rows
        for c in [f"{COL_LAT}_gt", f"{COL_LON}_gt", f"{COL_LAT}_pred", f"{COL_LON}_pred"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        before = len(df)
        df = df.dropna(subset=[f"{COL_LAT}_gt", f"{COL_LON}_gt", f"{COL_LAT}_pred", f"{COL_LON}_pred"]).copy()
        after = len(df)

        if after == 0:
            raise ValueError(f"{model}: all rows dropped due to missing/invalid lat/lon after numeric coercion.")
        # (optional) print(f"{model}: dropped {before-after} rows with invalid lat/lon")


        # distance + correctness
        df["dist_km"] = haversine_km(df[f"{COL_LAT}_gt"], df[f"{COL_LON}_gt"],
                                    df[f"{COL_LAT}_pred"], df[f"{COL_LON}_pred"])
        df["correct"] = (df["dist_km"] <= ACC_KM).astype(int)

        # certainty
        df["certainty"] = df[COL_REASON].apply(combined_certainty)

        # associations
        spearman = df[["certainty", "dist_km"]].corr(method="spearman").iloc[0, 1]
        spearman_neg = float(-spearman) if pd.notna(spearman) else np.nan

        auc = np.nan
        if df["correct"].nunique() == 2:
            auc = float(roc_auc_score(df["correct"], df["certainty"]))

        ece = ece_score(df["correct"].values, df["certainty"].values, n_bins=N_BINS)

        # selective acc
        cover_pts = np.array([0.1, 0.2, 0.5, 1.0])
        _, ys = selective_accuracy_curve(df["correct"].values, df["certainty"].values, coverages=cover_pts)
        acc_top10, acc_top20, acc_top50, acc_all = ys.tolist()

        # reliability bins
        rel = binned_reliability(df["correct"].values, df["certainty"].values, n_bins=N_BINS)
        rel.to_csv(os.path.join(OUT_DIR, f"reliability_bins_{model}.csv"), index=False)

        ax = axes[idx]
        ax.plot(rel["mean_score"], rel["acc"], marker="o", linewidth=1.5)
        ax.set_title(model, fontsize=10)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.25)
        ax.set_xlabel("Certainty score")
        ax.set_ylabel(f"Empirical Acc@{int(ACC_KM)}km")

        # combined risk–coverage curve
        xs_full = np.linspace(0.1, 1.0, 10)
        x, y = selective_accuracy_curve(df["correct"].values, df["certainty"].values, coverages=xs_full)
        curves.append(pd.DataFrame({"model": model, "coverage": x, "accuracy": y}))

        summary_rows.append({
            "model": model,
            "n": int(len(df)),
            f"acc@{int(ACC_KM)}km": float(df["correct"].mean()),
            "median_dist_km": float(np.median(df["dist_km"])),
            "mean_certainty": float(df["certainty"].mean()),
            "spearman(-dist, certainty)": spearman_neg,
            "auc(correct|certainty)": auc,
            "ece": ece,
            "acc_top10%": float(acc_top10),
            "acc_top20%": float(acc_top20),
            "acc_top50%": float(acc_top50),
        })

    for j in range(n_models, len(axes)):
        axes[j].axis("off")

    fig_grid.suptitle(f"Reliability (binned) — Correct if dist ≤ {ACC_KM:.0f} km", y=1.01, fontsize=12)
    fig_grid.tight_layout()
    fig_grid.savefig(os.path.join(OUT_DIR, "reliability_grid.png"), dpi=200, bbox_inches="tight")
    plt.close(fig_grid)

    summary = pd.DataFrame(summary_rows).sort_values(by=f"acc@{int(ACC_KM)}km", ascending=False)
    summary.to_csv(os.path.join(OUT_DIR, "certainty_summary.csv"), index=False)

    curves_df = pd.concat(curves, ignore_index=True)
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=curves_df, x="coverage", y="accuracy", hue="model", linewidth=2)
    plt.title(f"Risk–coverage: Acc@{int(ACC_KM)}km vs coverage (top-c by certainty)")
    plt.xlabel("Coverage (keep top-c most certain predictions)")
    plt.ylabel(f"Accuracy@{int(ACC_KM)}km on retained set")
    plt.ylim(0, 1)
    plt.xlim(0.1, 1.0)
    plt.grid(True, alpha=0.25)
    plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0, fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "risk_coverage_curves.png"), dpi=200, bbox_inches="tight")
    plt.close()

    print(f"[OK] Wrote outputs to: {OUT_DIR}")
    print(f" - certainty_summary.csv")
    print(f" - risk_coverage_curves.png")
    print(f" - reliability_grid.png")
    print(f" - reliability_bins_<model>.csv (per model)")

if __name__ == "__main__":
    main()
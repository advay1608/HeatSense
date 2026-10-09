"""
07_visualizations.py
----------------------
OWNER: Person 4  (see assignments/PERSON4.md)
WRITES: PNG files to backend/output/figures/
READS:  backend/data/dataset.csv, results.json (all sections)

Generates all 6 required report figures:
  1. Histogram + fitted distribution curve
  2. Boxplot
  3. Q-Q plot
  4. Monte Carlo convergence plot
  5. Threshold sensitivity curve
  6. Autocorrelation plot
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from common import load_temps, read_results

plt.rcParams["figure.dpi"] = 110
FIG_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "figures")

DIST_LOOKUP = {
    "normal": stats.norm,
    "lognorm": stats.lognorm,
    "gamma": stats.gamma,
    "gumbel_r": stats.gumbel_r,
}


def ensure_fig_dir():
    os.makedirs(FIG_DIR, exist_ok=True)


def fig1_histogram(temps, dist_fit):
    best_name = dist_fit["best_model"]
    dist = DIST_LOOKUP[best_name]
    params = tuple(dist_fit["candidates"][
        [c["name"] for c in dist_fit["candidates"]].index(best_name)
    ]["params"].values())
    threshold = dist_fit["threshold_c"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bins = 35 if len(temps) > 500 else 10
    ax.hist(temps, bins=bins, density=True, alpha=0.6, color="#4C72B0",
            edgecolor="white", label="Observed daily max temps")
    x = np.linspace(temps.min() - 3, temps.max() + 3, 500)
    y = dist.pdf(x, *params)
    ax.plot(x, y, color="#C44E52", linewidth=2, label=f"Fitted {best_name}")
    x_shade = np.linspace(threshold, x.max(), 200)
    y_shade = dist.pdf(x_shade, *params)
    ax.fill_between(x_shade, y_shade, color="#C44E52", alpha=0.3,
                     label=f"P(temp > {threshold}C)")
    ax.axvline(threshold, color="#C44E52", linestyle="--", linewidth=1)
    ax.set_xlabel("Max Temperature (C)")
    ax.set_ylabel("Density")
    ax.set_title(f"Temperature Distribution — Best Fit: {best_name}")
    ax.legend()
    fig.tight_layout()
    path = os.path.join(FIG_DIR, "01_histogram.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"Saved -> {path}")


def fig2_boxplot(temps):
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.boxplot(temps, vert=True, patch_artist=True,
               boxprops=dict(facecolor="#4C72B0", alpha=0.6),
               medianprops=dict(color="black", linewidth=2))
    ax.set_ylabel("Max Temperature (C)")
    ax.set_title("Boxplot of Daily Max Temperatures")
    ax.set_xticklabels(["All observed days"])
    fig.tight_layout()
    path = os.path.join(FIG_DIR, "02_boxplot.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"Saved -> {path}")


def fig3_qq(temps):
    fig, ax = plt.subplots(figsize=(6, 6))
    stats.probplot(temps, dist="norm", plot=ax)
    ax.set_title("Q-Q Plot vs. Normal Distribution")
    fig.tight_layout()
    path = os.path.join(FIG_DIR, "03_qqplot.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"Saved -> {path}")


def fig4_convergence(sim):
    fig, ax = plt.subplots(figsize=(7, 5))
    trials = sim["monte_carlo"]["trials"]
    probs = sim["monte_carlo"]["probabilities"]
    ax.plot(trials, probs, marker="o", color="#4C72B0", label="Monte Carlo estimate")
    ax.axhline(sim["comparison"]["theoretical"], color="#C44E52", linestyle="--",
               label=f"Theoretical ({sim['comparison']['theoretical']})")
    ax.set_xscale("log")
    ax.set_xlabel("Number of Monte Carlo trials (log scale)")
    ax.set_ylabel("Estimated P(temp > threshold)")
    ax.set_title("Monte Carlo Convergence")
    ax.legend()
    fig.tight_layout()
    path = os.path.join(FIG_DIR, "04_convergence.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"Saved -> {path}")


def fig5_sensitivity(sim):
    fig, ax = plt.subplots(figsize=(7, 5))
    thr = sim["threshold_sensitivity"]["thresholds_c"]
    probs = sim["threshold_sensitivity"]["probabilities"]
    ax.plot(thr, probs, marker="o", color="#55A868")
    ax.axvline(sim["threshold_c"], color="#C44E52", linestyle="--", alpha=0.7)
    ax.set_xlabel("Threshold (C)")
    ax.set_ylabel("P(temp > threshold)")
    ax.set_title("Threshold Sensitivity")
    fig.tight_layout()
    path = os.path.join(FIG_DIR, "05_sensitivity.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"Saved -> {path}")


def fig6_autocorrelation(temps):
    fig, ax = plt.subplots(figsize=(7, 5))
    n_lags = min(15, len(temps) // 2)
    lags = range(1, n_lags + 1)
    acf_vals = [np.corrcoef(temps[:-lag], temps[lag:])[0, 1] for lag in lags]
    ax.bar(lags, acf_vals, color="#4C72B0", alpha=0.7)
    bound = 1.96 / np.sqrt(len(temps))
    ax.axhline(bound, color="#C44E52", linestyle="--", linewidth=1)
    ax.axhline(-bound, color="#C44E52", linestyle="--", linewidth=1)
    ax.set_xlabel("Lag (days)")
    ax.set_ylabel("Autocorrelation")
    ax.set_title("Autocorrelation Function")
    fig.tight_layout()
    path = os.path.join(FIG_DIR, "06_autocorrelation.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"Saved -> {path}")


def main():
    ensure_fig_dir()
    temps = load_temps()
    results = read_results()

    required = ["distribution_fit", "simulation"]
    missing = [r for r in required if r not in results]
    if missing:
        raise RuntimeError(
            f"Cannot generate all figures — missing sections: {missing}. "
            f"Run run_pipeline.py first."
        )

    fig1_histogram(temps, results["distribution_fit"])
    fig2_boxplot(temps)
    fig3_qq(temps)
    fig4_convergence(results["simulation"])
    fig5_sensitivity(results["simulation"])
    fig6_autocorrelation(temps)

    print("\nAll figures generated.")


if __name__ == "__main__":
    main()

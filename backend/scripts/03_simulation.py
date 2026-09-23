"""
03_simulation.py
------------------
OWNER: Person 5  (see assignments/PERSON5.md)
WRITES: results.json["simulation"]
READS:  backend/data/dataset.csv, results.json["distribution_fit"] (REQUIRED)

Monte Carlo simulation (with convergence check), bootstrap probability
estimate, return period, and threshold sensitivity curve. Uses ONLY the
canonical best-fit model and threshold from distribution_fit — never
refits its own distribution or picks its own threshold.
"""

import numpy as np
from scipy import stats
from common import load_temps, read_results, write_result

RANDOM_SEED = 42
TRIAL_SIZES = [1_000, 10_000, 100_000]
BOOTSTRAP_RESAMPLES = 10_000

DIST_LOOKUP = {
    "normal": stats.norm,
    "lognorm": stats.lognorm,
    "gamma": stats.gamma,
    "gumbel_r": stats.gumbel_r,
}


def require_distribution_fit() -> dict:
    results = read_results()
    if "distribution_fit" not in results:
        raise RuntimeError(
            "results.json has no 'distribution_fit' section yet.\n"
            "Run backend/scripts/02_distribution_fit.py first (Person 1's script)."
        )
    return results["distribution_fit"]


def monte_carlo_probability(dist, params: tuple, threshold: float,
                             n_trials: int, seed: int) -> float:
    simulated = dist.rvs(*params, size=n_trials, random_state=seed)
    return float(np.mean(simulated > threshold))


def bootstrap_probability(temps: np.ndarray, threshold: float,
                           n_resamples: int = BOOTSTRAP_RESAMPLES,
                           seed: int = RANDOM_SEED) -> float:
    rng = np.random.default_rng(seed)
    n = len(temps)
    fractions = np.empty(n_resamples)
    for i in range(n_resamples):
        resample = rng.choice(temps, size=n, replace=True)
        fractions[i] = np.mean(resample > threshold)
    return float(np.mean(fractions))


def main():
    temps = load_temps()
    dist_fit = require_distribution_fit()

    threshold = dist_fit["threshold_c"]
    best_name = dist_fit["best_model"]
    best_params_dict = next(c["params"] for c in dist_fit["candidates"] if c["name"] == best_name)
    dist = DIST_LOOKUP[best_name]
    params = tuple(best_params_dict.values())

    theoretical_p = dist_fit["theoretical_probability"]

    mc_probs = [
        monte_carlo_probability(dist, params, threshold, n, RANDOM_SEED)
        for n in TRIAL_SIZES
    ]

    boot_p = bootstrap_probability(temps, threshold)

    return_period = round(1 / theoretical_p, 1) if theoretical_p > 0 else None

    sens_thresholds = [round(threshold + d, 1) for d in [-3, -2, -1, 0, 1, 2]]
    sens_probs = [round(float(dist.sf(t, *params)), 4) for t in sens_thresholds]

    result = {
        "threshold_c": threshold,
        "monte_carlo": {
            "trials": TRIAL_SIZES,
            "probabilities": [round(p, 4) for p in mc_probs],
        },
        "bootstrap_probability": round(boot_p, 4),
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "comparison": {
            "theoretical": theoretical_p,
            "monte_carlo_10k": round(mc_probs[1], 4),
            "bootstrap": round(boot_p, 4),
        },
        "return_period_days": return_period,
        "threshold_sensitivity": {
            "thresholds_c": sens_thresholds,
            "probabilities": sens_probs,
        },
    }

    print("=== SIMULATION & PROBABILITY CROSS-CHECKS ===")
    print(f"Theoretical: {theoretical_p:.4f}  Monte Carlo (10k): {mc_probs[1]:.4f}  "
          f"Bootstrap: {boot_p:.4f}")
    print(f"Return period: ~1-in-{return_period}-day event")
    print(f"Convergence across trials: {list(zip(TRIAL_SIZES, [round(p,4) for p in mc_probs]))}")

    write_result("simulation", result)
    return result


if __name__ == "__main__":
    main()

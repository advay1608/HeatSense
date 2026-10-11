"""
03_simulation.py
-----------------
OWNER: Person 5  (see assignments/PERSON5.md)
WRITES: results.json["simulation"]
READS:  backend/data/dataset.csv, results.json["distribution_fit"]

Cross-validates theoretical exceedance probabilities using:
1. Parametric Monte Carlo simulation from the fitted model across 1k, 10k, and 100k trials.
2. Non-parametric bootstrap resampling with replacement directly from observed data.
3. Compares empirical baseline against theoretical and simulation estimates.
4. Computes return periods and threshold sensitivity curves.
"""

import os
import sys
import numpy as np
from scipy import stats

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
from common import load_temps, read_results, write_result

RANDOM_SEED = 42
MONTE_CARLO_TRIALS = [1000, 10000, 100000]
BOOTSTRAP_RESAMPLES = 10000

DIST_MAP = {
    "normal": stats.norm,
    "norm": stats.norm,
    "lognorm": stats.lognorm,
    "gamma": stats.gamma,
    "gumbel_r": stats.gumbel_r,
}


def get_scipy_dist(dist_name: str):
    if dist_name in DIST_MAP:
        return DIST_MAP[dist_name]
    if hasattr(stats, dist_name):
        return getattr(stats, dist_name)
    raise ValueError(f"Unknown distribution model: '{dist_name}'. Supported: {list(DIST_MAP.keys())}")


def extract_best_params(dist_fit: dict, best_model_name: str):
    candidates = dist_fit.get("candidates", [])
    raw_params = None

    if isinstance(candidates, list):
        for candidate in candidates:
            name = candidate.get("name") or candidate.get("model") or candidate.get("distribution")
            if name == best_model_name:
                raw_params = candidate.get("params")
                break
    elif isinstance(candidates, dict):
        if best_model_name in candidates:
            raw_params = candidates[best_model_name].get("params")

    if raw_params is None:
        raise KeyError(f"Could not find parameters for best model '{best_model_name}' in candidates.")
    return raw_params


def sample_from_dist(dist, params, size: int, seed: int) -> np.ndarray:
    if isinstance(params, dict):
        clean_params = {k: float(v) for k, v in params.items()}
        return dist.rvs(**clean_params, size=size, random_state=seed)
    elif isinstance(params, (list, tuple)):
        clean_params = [float(p) for p in params]
        return dist.rvs(*clean_params, size=size, random_state=seed)
    else:
        return dist.rvs(float(params), size=size, random_state=seed)


def sf_from_dist(dist, params, x: float) -> float:
    if isinstance(params, dict):
        clean_params = {k: float(v) for k, v in params.items()}
        return float(dist.sf(x, **clean_params))
    elif isinstance(params, (list, tuple)):
        clean_params = [float(p) for p in params]
        return float(dist.sf(x, *clean_params))
    else:
        return float(dist.sf(x, float(params)))


def main():
    results = read_results()
    if "distribution_fit" not in results:
        raise RuntimeError(
            "Could not find 'distribution_fit' in results.json. "
            "Please run 02_distribution_fit.py first."
        )

    dist_fit = results["distribution_fit"]
    best_model_name = dist_fit["best_model"]
    threshold_c = float(dist_fit["threshold_c"])
    theoretical_prob = float(dist_fit["theoretical_probability"])
    empirical_prob = float(dist_fit.get("empirical_probability", 0.0))

    raw_params = extract_best_params(dist_fit, best_model_name)
    dist = get_scipy_dist(best_model_name)
    temps = load_temps()
    n_obs = len(temps)

    print("=== SIMULATION & PROBABILITY CROSS-CHECKS ===")
    print(f"Fitted model: {best_model_name}")
    print(f"Canonical threshold: {threshold_c:.1f} C (rule: temp > threshold)")
    print(f"Empirical P(temp > {threshold_c:.1f} C): {empirical_prob:.4f} (direct observed baseline)")
    print(f"Theoretical P(temp > {threshold_c:.1f} C): {theoretical_prob:.4f} (parametric {best_model_name})")

    # 1. Monte Carlo Simulation (1k, 10k, 100k trials)
    print("\n--- Monte Carlo Simulation (Parametric, Fitted Model) ---")
    mc_probs = []
    for n in MONTE_CARLO_TRIALS:
        samples = sample_from_dist(dist, raw_params, size=n, seed=RANDOM_SEED)
        exceed_fraction = float(np.sum(samples > threshold_c) / n)
        mc_probs.append(round(exceed_fraction, 4))
        diff = exceed_fraction - theoretical_prob
        print(f"  {n:>7,d} trials: {exceed_fraction:.4f} (diff from theoretical: {diff:+.4f})")

    # 2. Bootstrap Probability Resampling
    print("\n--- Bootstrap Resampling (Non-Parametric, Real Recorded Data) ---")
    rng = np.random.default_rng(RANDOM_SEED)
    batch_size = 1000
    boot_fractions = []
    for _ in range(BOOTSTRAP_RESAMPLES // batch_size):
        sub_matrix = rng.choice(temps, size=(batch_size, n_obs), replace=True)
        boot_fractions.extend(np.mean(sub_matrix > threshold_c, axis=1))
    bootstrap_prob = round(float(np.mean(boot_fractions)), 4)
    boot_ci95 = [round(float(np.percentile(boot_fractions, 2.5)), 4), round(float(np.percentile(boot_fractions, 97.5)), 4)]
    print(f"  {BOOTSTRAP_RESAMPLES:,d} resamples: {bootstrap_prob:.4f} (95% CI [{boot_ci95[0]:.4f}, {boot_ci95[1]:.4f}])")

    # 3. Side-by-Side Comparison
    mc_10k_prob = mc_probs[1]
    comparison = {
        "empirical_baseline": empirical_prob,
        "theoretical": theoretical_prob,
        "monte_carlo_10k": mc_10k_prob,
        "bootstrap": bootstrap_prob,
    }
    print("\n--- Probability Comparison ---")
    print(f"  Empirical Baseline (raw data) : {comparison['empirical_baseline']:.4f}")
    print(f"  Theoretical (fitted model)   : {comparison['theoretical']:.4f}")
    print(f"  Monte Carlo (10k trials)     : {comparison['monte_carlo_10k']:.4f}")
    print(f"  Bootstrap (10k resamples)    : {comparison['bootstrap']:.4f}")

    # 4. Return Period Calculation
    chosen_prob = empirical_prob if empirical_prob > 0 else mc_10k_prob
    if chosen_prob > 0:
        return_period_days = round(1.0 / chosen_prob, 1)
    else:
        return_period_days = float("inf")
    print(f"\nReturn Period (based on empirical rate): ~1-in-{return_period_days:.1f}-day event")

    # 5. Threshold Sensitivity (evaluated on both empirical data and parametric survival function)
    # Steps: 28°C to 44°C
    thresholds_range = [round(float(t), 1) for t in range(28, 45, 2)]
    sensitivity_probs = []
    sensitivity_empirical = []
    print("\n--- Threshold Sensitivity ---")
    for t in thresholds_range:
        p_param = round(sf_from_dist(dist, raw_params, t), 4)
        p_emp = round(float(np.sum(temps > t) / n_obs), 4)
        sensitivity_probs.append(p_param)
        sensitivity_empirical.append(p_emp)
        flag = " <-- canonical" if abs(t - threshold_c) < 1e-4 else ""
        print(f"  Threshold {t:>4.1f} C: Parametric = {p_param:.4f} | Empirical = {p_emp:.4f}{flag}")

    simulation_data = {
        "threshold_c": threshold_c,
        "exceedance_rule": "temperature > threshold_c",
        "monte_carlo": {
            "model_sampled": best_model_name,
            "trials": MONTE_CARLO_TRIALS,
            "probabilities": mc_probs,
            "note": f"Parametric random draws from fitted {best_model_name} distribution at canonical threshold {threshold_c:.1f}°C. Validates numerical convergence of theoretical SF, not independent empirical model correctness.",
        },
        "bootstrap_probability": bootstrap_prob,
        "bootstrap_ci95": boot_ci95,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "comparison": comparison,
        "return_period_days": return_period_days,
        "recurrence_note": "Inverse of long-run empirical exceedance rate (average historical spacing). Extreme heat clusters in multi-day events, so this does not represent a periodic schedule.",
        "threshold_sensitivity": {
            "thresholds_c": thresholds_range,
            "probabilities": sensitivity_probs,
            "empirical_probabilities": sensitivity_empirical,
        },
    }

    write_result("simulation", simulation_data)
    return simulation_data


if __name__ == "__main__":
    main()
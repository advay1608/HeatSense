"""
03_simulation.py
-----------------
OWNER: Person 5  (see assignments/PERSON5.md)
WRITES: results.json["simulation"]
READS:  backend/data/dataset.csv, results.json["distribution_fit"]
        — distribution_fit MUST exist before running this script.

Stress-tests the theoretical probability from Person 1 (02_distribution_fit.py)
using two independent cross-checks:
1. Monte Carlo simulation: parametric simulation from the fitted distribution
   across 1k, 10k, and 100k trials to verify convergence.
2. Bootstrap resampling: non-parametric empirical estimation with replacement
   directly from the recorded temperatures (no distribution assumptions).

Also computes the return period in days (risk framing) and threshold sensitivity
across a range of temperatures around the canonical threshold.
"""

import os
import sys
import numpy as np
from scipy import stats

# Ensure backend/scripts is on the Python path regardless of where script is invoked
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_temps, read_results, write_result

RANDOM_SEED = 42
MONTE_CARLO_TRIALS = [1000, 10000, 100000]
BOOTSTRAP_RESAMPLES = 10000

# Map distribution names used by Person 1 to scipy.stats distribution objects
DIST_MAP = {
    "normal": stats.norm,
    "norm": stats.norm,
    "lognorm": stats.lognorm,
    "gamma": stats.gamma,
    "gumbel_r": stats.gumbel_r,
}


def get_scipy_dist(dist_name: str):
    """Retrieve scipy.stats distribution object for a model name."""
    if dist_name in DIST_MAP:
        return DIST_MAP[dist_name]
    if hasattr(stats, dist_name):
        return getattr(stats, dist_name)
    raise ValueError(f"Unknown distribution model: '{dist_name}'. Supported: {list(DIST_MAP.keys())}")


def extract_best_params(dist_fit: dict, best_model_name: str):
    """Extract fitted parameters for the best model from candidates list or dict."""
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
        raise KeyError(
            f"Could not find parameters for best model '{best_model_name}' "
            f"in results.json['distribution_fit']['candidates']."
        )
    return raw_params


def sample_from_dist(dist, params, size: int, seed: int) -> np.ndarray:
    """Generate random variates from scipy distribution given dict or tuple params."""
    if isinstance(params, dict):
        clean_params = {k: float(v) for k, v in params.items()}
        return dist.rvs(**clean_params, size=size, random_state=seed)
    elif isinstance(params, (list, tuple)):
        clean_params = [float(p) for p in params]
        return dist.rvs(*clean_params, size=size, random_state=seed)
    else:
        return dist.rvs(float(params), size=size, random_state=seed)


def sf_from_dist(dist, params, x: float) -> float:
    """Compute survival function (1 - CDF) for scipy distribution given dict or tuple params."""
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
            "\n\nCould not find 'distribution_fit' in results.json.\n"
            "This section is Person 1's deliverable (backend/scripts/02_distribution_fit.py).\n"
            "Please run 02_distribution_fit.py first, or run run_pipeline.py to execute the full pipeline.\n"
        )

    dist_fit = results["distribution_fit"]
    best_model_name = dist_fit["best_model"]
    threshold_c = float(dist_fit["threshold_c"])
    theoretical_prob = float(dist_fit["theoretical_probability"])

    raw_params = extract_best_params(dist_fit, best_model_name)
    dist = get_scipy_dist(best_model_name)

    print("=== SIMULATION & PROBABILITY CROSS-CHECKS ===")
    print(f"Fitted model: {best_model_name}")
    print(f"Canonical threshold: {threshold_c:.1f} C")
    print(f"Theoretical P(temp > {threshold_c:.1f} C): {theoretical_prob:.4f}")

    # 1. Monte Carlo Simulation (Convergence Analysis across 1k, 10k, 100k trials)
    print("\n--- Monte Carlo Simulation (Parametric, Fitted Model) ---")
    mc_probs = []
    for n in MONTE_CARLO_TRIALS:
        samples = sample_from_dist(dist, raw_params, size=n, seed=RANDOM_SEED)
        exceed_fraction = float(np.sum(samples > threshold_c) / n)
        mc_probs.append(round(exceed_fraction, 4))
        diff = exceed_fraction - theoretical_prob
        print(f"  {n:>7,d} trials: {exceed_fraction:.4f}  (diff from theoretical: {diff:+.4f})")

    # 2. Bootstrap Probability (Distribution-Free Non-Parametric Resampling)
    print("\n--- Bootstrap Resampling (Non-Parametric, Real Recorded Data) ---")
    temps = load_temps()
    rng = np.random.default_rng(RANDOM_SEED)
    # Resample with replacement 10,000 times (in batches to maintain low memory footprint)
    batch_size = 1000
    boot_fractions = []
    for _ in range(BOOTSTRAP_RESAMPLES // batch_size):
        sub_matrix = rng.choice(temps, size=(batch_size, len(temps)), replace=True)
        boot_fractions.extend(np.mean(sub_matrix > threshold_c, axis=1))
    bootstrap_prob = round(float(np.mean(boot_fractions)), 4)
    print(f"  {BOOTSTRAP_RESAMPLES:,d} resamples: {bootstrap_prob:.4f}")

    # 3. Side-by-Side Comparison
    mc_10k_prob = mc_probs[1]
    comparison = {
        "theoretical": theoretical_prob,
        "monte_carlo_10k": mc_10k_prob,
        "bootstrap": bootstrap_prob,
    }
    print("\n--- Probability Comparison ---")
    print(f"  Theoretical (Person 1 fit) : {comparison['theoretical']:.4f}")
    print(f"  Monte Carlo (10k trials)   : {comparison['monte_carlo_10k']:.4f}")
    print(f"  Bootstrap (raw data)       : {comparison['bootstrap']:.4f}")

    # 4. Return Period Calculation
    # Using 10k Monte Carlo figure (as specified in assignment option; documented here)
    chosen_prob = mc_10k_prob
    if chosen_prob > 0:
        return_period_days = round(1.0 / chosen_prob, 1)
    else:
        return_period_days = float("inf")
    print(f"\nReturn Period (based on 10k MC): ~1-in-{return_period_days:.1f}-day event")

    # 5. Threshold Sensitivity (Evaluating survival function across range around canonical threshold)
    # Step every 1 C from threshold_c - 3 to threshold_c + 2
    thresholds_range = [round(threshold_c + offset, 1) for offset in range(-3, 3)]
    sensitivity_probs = []
    print("\n--- Threshold Sensitivity ---")
    for t in thresholds_range:
        prob = round(sf_from_dist(dist, raw_params, t), 4)
        sensitivity_probs.append(prob)
        flag = " <-- canonical" if abs(t - threshold_c) < 1e-4 else ""
        print(f"  Threshold {t:>4.1f} C: P(temp > threshold) = {prob:.4f}{flag}")

    # Output schema matching ARCHITECTURE.md SS3 and assignments/PERSON5.md SS4
    simulation_data = {
        "threshold_c": threshold_c,
        "monte_carlo": {
            "trials": MONTE_CARLO_TRIALS,
            "probabilities": mc_probs,
        },
        "bootstrap_probability": bootstrap_prob,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "comparison": comparison,
        "return_period_days": return_period_days,
        "threshold_sensitivity": {
            "thresholds_c": thresholds_range,
            "probabilities": sensitivity_probs,
        },
    }

    # Write merged result back via common.write_result
    write_result("simulation", simulation_data)
    return simulation_data


if __name__ == "__main__":
    main()
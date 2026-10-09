"""
02_distribution_fit.py
------------------------
OWNER: Person 1  (see assignments/PERSON1.md)
WRITES: results.json["distribution_fit"]
READS:  backend/data/dataset.csv, results.json["core_stats"] (optional sanity check)

Fits Normal, Log-Normal, Gamma, and Gumbel distributions via MLE, compares
them with AIC/BIC, validates the winner on a holdout split, and computes
the canonical theoretical probability of exceeding the extreme-heat
threshold. THIS SCRIPT SETS THE CANONICAL threshold_c EVERY OTHER SCRIPT
MUST READ — do not let another script define its own.
"""

import numpy as np
from scipy import stats
from common import load_temps, write_result

RANDOM_SEED = 42
THRESHOLD_C = 36.0  # <-- the ONE canonical threshold for the whole project

CANDIDATES = {
    "normal": stats.norm,
    "lognorm": stats.lognorm,
    "gamma": stats.gamma,
    "gumbel_r": stats.gumbel_r,
}


def fit_and_score(dist, data: np.ndarray) -> dict:
    params = dist.fit(data)
    log_likelihood = np.sum(dist.logpdf(data, *params))
    k = len(params)
    n = len(data)
    aic = 2 * k - 2 * log_likelihood
    bic = k * np.log(n) - 2 * log_likelihood
    return {"params": params, "log_likelihood": log_likelihood, "aic": aic, "bic": bic}


def params_to_dict(dist_name: str, params: tuple) -> dict:
    """Best-effort readable param names per distribution; falls back to generic."""
    if dist_name == "normal":
        return {"loc": round(params[0], 4), "scale": round(params[1], 4)}
    if dist_name == "gumbel_r":
        return {"loc": round(params[0], 4), "scale": round(params[1], 4)}
    if dist_name == "lognorm":
        return {"s": round(params[0], 4), "loc": round(params[1], 4), "scale": round(params[2], 4)}
    if dist_name == "gamma":
        return {"a": round(params[0], 4), "loc": round(params[1], 4), "scale": round(params[2], 4)}
    return {"raw": [round(p, 4) for p in params]}


def holdout_validation(temps: np.ndarray, best_name: str, runner_up_name: str,
                        seed: int = RANDOM_SEED) -> dict:
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(temps))
    split = int(len(temps) * 0.8)
    train, test = temps[idx[:split]], temps[idx[split:]]

    def test_ll(name):
        dist = CANDIDATES[name]
        params = dist.fit(train)
        return float(np.sum(dist.logpdf(test, *params)))

    return {
        "train_size": int(len(train)),
        "test_size": int(len(test)),
        "best_model_test_log_likelihood": round(test_ll(best_name), 3),
        "runner_up_test_log_likelihood": round(test_ll(runner_up_name), 3),
    }


def main():
    temps = load_temps()

    scored = {}
    for name, dist in CANDIDATES.items():
        scored[name] = fit_and_score(dist, temps)

    candidates_out = []
    for name, s in scored.items():
        candidates_out.append({
            "name": name,
            "params": params_to_dict(name, s["params"]),
            "aic": round(float(s["aic"]), 2),
            "bic": round(float(s["bic"]), 2),
            "log_likelihood": round(float(s["log_likelihood"]), 2),
        })

    ranked = sorted(candidates_out, key=lambda c: c["aic"])
    best_name = ranked[0]["name"]
    runner_up_name = ranked[1]["name"]

    holdout = holdout_validation(temps, best_name, runner_up_name)

    qq = stats.probplot(temps, dist="norm")
    qq_r = qq[1][2]

    # Check if canonical threshold is within sensible bounds of the dataset
    threshold_c = THRESHOLD_C
    if temps.max() <= threshold_c or temps.min() >= threshold_c:
        threshold_c = round(float(np.percentile(temps, 90)), 1)
        print(f"Notice: Canonical 36.0C outside range [{temps.min():.1f}, {temps.max():.1f}] — using 90th percentile: {threshold_c}C")

    best_dist = CANDIDATES[best_name]
    best_params = scored[best_name]["params"]
    theoretical_probability = float(best_dist.sf(threshold_c, *best_params))

    result = {
        "threshold_c": threshold_c,
        "candidates": candidates_out,
        "best_model": best_name,
        "holdout_validation": holdout,
        "qq_plot_r_value": round(float(qq_r), 4),
        "theoretical_probability": round(theoretical_probability, 4),
    }

    print("=== DISTRIBUTION FIT ===")
    for c in ranked:
        print(f"  {c['name']:>10}: AIC={c['aic']:.2f}  BIC={c['bic']:.2f}")
    print(f"Best model: {best_name}")
    print(f"Holdout test log-likelihood — best: {holdout['best_model_test_log_likelihood']}, "
          f"runner-up: {holdout['runner_up_test_log_likelihood']}")
    print(f"P(temp > {threshold_c}C) under {best_name} = {theoretical_probability:.4f}")

    write_result("distribution_fit", result)
    return result


if __name__ == "__main__":
    main()

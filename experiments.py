from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from model import WasteCityModel

OUTPUT_DIR = Path('output')
OUTPUT_DIR.mkdir(exist_ok=True)


def run_scenario(name, steps=120, runs=5, **params):
    frames = []
    for run in range(runs):
        model = WasteCityModel(**params, seed=run)
        df = model.run_model(steps=steps).copy()
        df['step'] = range(len(df))
        df['run'] = run
        df['scenario'] = name
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def plot_metric(results, metric):
    summary = results.groupby(['scenario', 'step'])[metric].mean().reset_index()
    plt.figure(figsize=(10, 6))
    for scenario in summary['scenario'].unique():
        subset = summary[summary['scenario'] == scenario]
        plt.plot(subset['step'], subset[metric], label=scenario)
    plt.xlabel('Step')
    plt.ylabel(metric)
    plt.title(metric.replace('_', ' ').title())
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / f'{metric}.png', dpi=200)
    plt.close()


def main():
    # Baseline: n_bins=10 (8 district bins + 2 central bins)
    # few_bins=6  (district only, no central coverage)
    # many_bins=16 (district + dense central coverage)
    scenarios = {
        'few_bins':            dict(n_bins=6),
        'baseline_bins':       dict(n_bins=10),
        'many_bins':           dict(n_bins=16),
        'low_tourists':        dict(n_tourists=5),
        'high_tourists':       dict(n_tourists=20),
        'random_cleaning':     dict(cleaner_strategy='random'),
        'nearest_cleaning':    dict(cleaner_strategy='nearest'),
        'fixed_cleaning':      dict(cleaner_strategy='fixed'),
        'rare_transporter':    dict(transporter_threshold=1.0),
        'frequent_transporter': dict(transporter_threshold=0.5),
        'smart_bins':          dict(smart_bins_enabled=True, transporter_threshold=0.8),
    }

    all_results = pd.concat(
        [run_scenario(name, **params) for name, params in scenarios.items()],
        ignore_index=True,
    )
    all_results.to_csv(OUTPUT_DIR / 'scenario_results.csv', index=False)

    for metric in [
        'total_waste_on_streets',
        'overflowing_bins',
        'avg_waste_per_district',
        'robot_cleaning_efficiency',
        'transporter_workload',
        'sensor_alerted_bins',
        'transporter_pickups',
    ]:
        plot_metric(all_results, metric)


if __name__ == '__main__':
    main()

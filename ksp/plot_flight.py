"""Графики по CSV из telemetry.py.

Запуск: python plot_flight.py flight_20261101_183000.csv
Картинки сохраняются рядом с CSV (имя_файла_*.png).
"""
import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt


def load(path):
    with open(path, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    cols = {}
    for key in rows[0]:
        try:
            cols[key] = [float(r[key]) for r in rows]
        except ValueError:
            cols[key] = [r[key] for r in rows]
    return cols


def save(fig, path, suffix):
    out = path.with_name(f'{path.stem}_{suffix}.png')
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    print(f'Сохранено: {out}')


def main():
    path = Path(sys.argv[1])
    d = load(path)
    t = d['met']

    fig, ax = plt.subplots(2, 2, figsize=(11, 7))
    ax[0, 0].plot(t, [h / 1000 for h in d['altitude_m']])
    ax[0, 0].set(title='Высота', xlabel='t, с', ylabel='h, км')
    ax[0, 1].plot(t, d['orbital_speed'], label='орбитальная')
    ax[0, 1].plot(t, d['surface_speed'], label='относительно поверхности')
    ax[0, 1].set(title='Скорость', xlabel='t, с', ylabel='v, м/с')
    ax[0, 1].legend()
    ax[1, 0].plot(t, [m / 1000 for m in d['mass_kg']])
    ax[1, 0].set(title='Масса', xlabel='t, с', ylabel='m, т')
    ax[1, 1].plot(t, d['pitch_deg'])
    ax[1, 1].set(title='Тангаж', xlabel='t, с', ylabel='угол, °')
    for a in ax.flat:
        a.grid(alpha=0.3)
    save(fig, path, 'overview')

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(t, [x / 1000 for x in d['apoapsis_alt_m']], label='апоцентр')
    ax.plot(t, [x / 1000 for x in d['periapsis_alt_m']], label='перицентр')
    ax.set(title='Параметры орбиты', xlabel='t, с', ylabel='км', ylim=(-700, 3000))
    ax.grid(alpha=0.3)
    ax.legend()
    save(fig, path, 'orbit')


if __name__ == '__main__':
    main()

"""Графики по CSV из telemetry.py, исправленная версия.

Запуск: python plot_flight_v2.py final3.csv
Что исправлено по сравнению с plot_flight.py:
  * строки после удара (масса = 0) выкинуты;
  * участок у Кербина и участок у Муны нарисованы отдельно
    (высота считается от разных тел, поэтому на общем графике был скачок);
  * апоцентр рисуется только для замкнутой орбиты (e < 1),
    на пролётных участках игра даёт отрицательный апоцентр.
"""
import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

C1, C2, MUTED = '#2a6fdb', '#e8772e', '#8a8f98'
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.titleweight': 'bold', 'lines.linewidth': 1.8})


def load(path):
    with open(path, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        d = {k: (float(v) if k != 'body' else v) for k, v in r.items()}
        if d['mass_kg'] == 0:      # аппарат уже разбился
            break
        out.append(d)
    return out


def col(rows, key, k=1.0):
    return [r[key] * k for r in rows]


def grid(ax):
    ax.grid(alpha=0.25)


def save(fig, folder, name):
    fig.tight_layout()
    p = folder / name
    fig.savefig(p, dpi=150)
    plt.close(fig)
    print('Сохранено:', p)


def main():
    path = Path(sys.argv[1])
    folder = Path(sys.argv[2]) if len(sys.argv) > 2 else path.parent
    rows = load(path)
    launch = next(i for i, r in enumerate(rows) if r['thrust_n'] > 0)
    rows = rows[max(launch - 1, 0):]
    kerbin = [r for r in rows if r['body'] == 'Kerbin']
    mun = [r for r in rows if r['body'] == 'Mun']
    t_soi = mun[0]['met']

    # 1. Выведение на орбиту (первые ~13 минут)
    asc = [r for r in kerbin if r['met'] <= 780]
    t = col(asc, 'met')
    seps = [asc[i]['met'] for i in range(1, len(asc)) if asc[i]['stage'] != asc[i - 1]['stage'] and asc[i]['met'] > 5]
    fig, ax = plt.subplots(2, 2, figsize=(11, 7))
    ax[0, 0].plot(t, col(asc, 'altitude_m', 1e-3), color=C1)
    ax[0, 0].set(title='Высота над Кербином', xlabel='время полёта, с', ylabel='h, км')
    ax[0, 1].plot(t, col(asc, 'orbital_speed'), color=C1, label='орбитальная')
    ax[0, 1].plot(t, col(asc, 'surface_speed'), color=C2, label='относительно поверхности')
    ax[0, 1].set(title='Скорость', xlabel='время полёта, с', ylabel='v, м/с')
    ax[0, 1].legend(frameon=False)
    ax[1, 0].plot(t, col(asc, 'mass_kg', 1e-3), color=C1)
    ax[1, 0].set(title='Масса ракеты', xlabel='время полёта, с', ylabel='m, т')
    ax[1, 1].plot(t, col(asc, 'pitch_deg'), color=C1)
    ax[1, 1].set(title='Тангаж (угол к горизонту)', xlabel='время полёта, с', ylabel='угол, °')
    for a in ax.flat:
        grid(a)
        for s in seps:
            a.axvline(s, color=MUTED, ls='--', lw=0.8)
    ax[1, 0].text(seps[0] + 8, ax[1, 0].get_ylim()[1] * 0.92,
                  'пунктир — отделение первой ступени', color=MUTED, fontsize=8)
    fig.suptitle('Выведение на орбиту Кербина', fontweight='bold')
    save(fig, folder, 'grafik_1_vyvedenie.png')

    # 2. Высота: у Кербина и у Муны отдельно
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(col(kerbin, 'met', 1 / 3600), col(kerbin, 'altitude_m', 1e-3), color=C1)
    ax[0].set(title='Удаление от Кербина', xlabel='время полёта, ч', ylabel='h, км')
    ax[1].plot(col(mun, 'met', 1 / 3600), col(mun, 'altitude_m', 1e-3), color=C1)
    ax[1].set(title='Высота над Муной', xlabel='время полёта, ч', ylabel='h, км')
    for a in ax:
        grid(a)
    fig.suptitle(f'Перелёт: в зону притяжения Муны аппарат вошёл через {t_soi / 3600:.1f} ч',
                 fontweight='bold')
    save(fig, folder, 'grafik_2_perelet.png')

    # 3. Параметры орбит
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    park = [r for r in kerbin if r['met'] <= 1690 and r['eccentricity'] < 1 and r['apoapsis_alt_m'] > 0]
    ax[0].plot(col(park, 'met'), col(park, 'apoapsis_alt_m', 1e-3), color=C1, label='апоцентр')
    ax[0].plot(col(park, 'met'), col(park, 'periapsis_alt_m', 1e-3), color=C2, label='перицентр')
    ax[0].axhline(70, color=MUTED, ls=':', lw=1)
    ax[0].text(0, 72, 'граница атмосферы 70 км', color=MUTED, fontsize=8)
    ax[0].set(title='Орбита Кербина до разгона к Муне', xlabel='время полёта, с', ylabel='км', ylim=(-50, 120))
    ax[0].legend(frameon=False, loc='lower right')
    i0 = next(i for i, r in enumerate(mun) if r['thrust_n'] > 0)          # начало торможения
    i1 = next(i for i in range(i0, len(mun)) if mun[i]['thrust_n'] == 0)   # конец торможения
    orb = mun[i1:]
    ax[1].plot(col(orb, 'met', 1 / 3600), col(orb, 'apoapsis_alt_m', 1e-3), color=C1, label='апоцентр')
    ax[1].plot(col(orb, 'met', 1 / 3600), col(orb, 'periapsis_alt_m', 1e-3), color=C2, label='перицентр')
    ax[1].axhline(0, color=MUTED, lw=1)
    ax[1].text(orb[0]['met'] / 3600, 4, 'поверхность Муны', color=MUTED, fontsize=8)
    ax[1].set(title='Орбита Муны после торможения', xlabel='время полёта, ч',
              ylabel='км', ylim=(-110, 130))
    ax[1].legend(frameon=False, loc='lower left')
    for a in ax:
        grid(a)
    save(fig, folder, 'grafik_3_orbity.png')

    # 4. Падение
    burn = max(i for i, r in enumerate(mun) if r['thrust_n'] > 0)
    fall = mun[burn - 5:]
    tt = [(r['met'] - fall[-1]['met']) / 60 for r in fall]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(tt, col(fall, 'surface_altitude_m', 1e-3), color=C1)
    ax[0].set(title='Высота над рельефом', xlabel='минут до удара', ylabel='h, км')
    ax[1].plot(tt, col(fall, 'latitude_deg'), color=C1)
    ax[1].axhline(-90, color=MUTED, ls=':', lw=1)
    ax[1].text(tt[0], -88, 'южный полюс (−90°)', color=MUTED, fontsize=8)
    last = fall[-1]
    ax[1].annotate(f'удар: {last["latitude_deg"]:.1f}°', (0, last['latitude_deg']),
                   xytext=(-25, 25), textcoords='offset points', fontsize=9,
                   arrowprops=dict(arrowstyle='-', color=MUTED))
    ax[1].set(title='Широта под аппаратом', xlabel='минут до удара', ylabel='широта, °')
    for a in ax:
        grid(a)
    fig.suptitle(f'Сход с орбиты и падение: удар на скорости {last["surface_speed"]:.0f} м/с',
                 fontweight='bold')
    save(fig, folder, 'grafik_4_padenie.png')


if __name__ == '__main__':
    main()

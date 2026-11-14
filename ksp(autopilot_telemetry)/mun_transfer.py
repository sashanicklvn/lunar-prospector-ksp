"""Перелёт с орбиты Kerbin к Муне через kRPC.

Аппарат на орбите Kerbin (любой, 75–150 км), сервер kRPC запущен. Запуск:
    python mun_transfer.py

Скрипт сам находит момент разгона, при котором траектория встречает Муну
с перицентром около TARGET_PE, ставит узел и выполняет его.
Перицентр потом уточняется коррекцией в mun_capture.py.
"""
import math
import time

from burn import connect, execute_node, describe_orbit

TARGET_PE = 100_000     # м, желаемая высота пролёта у Муны
SCAN_STEPS = 60         # сколько точек орбиты перебираем
DV_BUMPS = (0, 15, 30, 45, 60)   # добавки к dv Гомана, если встречи нет


def hohmann_dv(orbit, r2):
    mu = orbit.body.gravitational_parameter
    a1 = orbit.semi_major_axis
    v1 = math.sqrt(mu / a1)
    return v1 * (math.sqrt(2 * r2 / (a1 + r2)) - 1)


def mun_periapsis(node, mun):
    """Высота перицентра у Муны для узла, или None, если встречи нет."""
    nxt = node.orbit.next_orbit
    if nxt is None or nxt.body.name != mun.name:
        return None
    return nxt.periapsis_altitude


def find_transfer(conn, vessel):
    sc = conn.space_center
    orbit = vessel.orbit
    mun = sc.bodies['Mun']
    dv0 = hohmann_dv(orbit, mun.orbit.semi_major_axis)
    period = orbit.period
    print(f'dv Гомана: {dv0:.0f} м/с, период орбиты {period:.0f} с')

    for bump in DV_BUMPS:
        dv = dv0 + bump
        print(f'Ищем встречу при dv = {dv:.0f} м/с...')
        samples = []
        t0 = sc.ut + 120
        for i in range(SCAN_STEPS):
            ut = t0 + period * i / SCAN_STEPS
            node = vessel.control.add_node(ut, prograde=dv)
            pe = mun_periapsis(node, mun)
            node.remove()
            samples.append((ut, pe))
        hits = [(ut, pe) for ut, pe in samples if pe is not None]
        if not hits:
            continue
        print(f'  встреча есть в {len(hits)} точках из {SCAN_STEPS}')

        # Среди соседних точек ищем переход через TARGET_PE и уточняем делением пополам
        best = None
        for (ut_a, pe_a), (ut_b, pe_b) in zip(samples, samples[1:]):
            if pe_a is None or pe_b is None:
                continue
            if (pe_a - TARGET_PE) * (pe_b - TARGET_PE) > 0:
                continue
            lo, hi = ut_a, ut_b
            for _ in range(25):
                mid = (lo + hi) / 2
                node = vessel.control.add_node(mid, prograde=dv)
                pe_mid = mun_periapsis(node, mun)
                node.remove()
                if pe_mid is None:
                    break
                if (pe_a - TARGET_PE) * (pe_mid - TARGET_PE) <= 0:
                    hi, pe_b = mid, pe_mid
                else:
                    lo, pe_a = mid, pe_mid
            ut = (lo + hi) / 2
            node = vessel.control.add_node(ut, prograde=dv)
            pe = mun_periapsis(node, mun)
            node.remove()
            if pe is not None and (best is None or abs(pe - TARGET_PE) < abs(best[1] - TARGET_PE)):
                best = (ut, pe, dv)
        if best is None:
            # встреча есть, но нужной высоты не нашли: берём точку с наименьшим |pe - цель|
            ut, pe = min(hits, key=lambda s: abs(s[1] - TARGET_PE))
            best = (ut, pe, dv)
        return best
    return None


def main():
    conn, vessel = connect('Mun transfer')
    if vessel.orbit.body.name != 'Kerbin' or vessel.orbit.periapsis_altitude < 70_000:
        print('Нужна орбита вокруг Kerbin с перицентром выше 70 км. Сначала ascent.py.')
        return
    describe_orbit(vessel)

    found = find_transfer(conn, vessel)
    if found is None:
        print('Встречу с Муной найти не удалось. Проверь, что орбита близка к экваториальной.')
        return
    ut, pe, dv = found
    print(f'Узел: через {(ut - conn.space_center.ut) / 60:.1f} мин, dv = {dv:.0f} м/с, '
          f'перицентр у Муны ~{pe / 1000:.0f} км')
    node = vessel.control.add_node(ut, prograde=dv)

    if not execute_node(conn, vessel, node):
        return
    o = vessel.orbit
    nxt = o.next_orbit
    if nxt is not None and nxt.body.name == 'Mun':
        print(f'Летим к Муне: перицентр {nxt.periapsis_altitude / 1000:.0f} км, '
              f'вход в зону Муны через {o.time_to_soi_change / 3600:.1f} ч.')
        print('Дальше: python mun_capture.py')
    else:
        print('После разгона встречи нет. Поставь небольшую коррекцию вручную или '
              'запусти mun_capture.py: он попробует поймать Муну коррекцией.')
    time.sleep(1)


if __name__ == '__main__':
    main()

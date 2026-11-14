"""Коррекция на полпути к Муне (полярный пролёт) и торможение в полярную орбиту.

Аппарат летит к Муне после mun_transfer.py, сервер kRPC запущен. Запуск:
    python mun_capture.py

Шаг 1. Узел на половине пути до зоны Муны. Подбираем нормальную и радиальную
        составляющие так, чтобы пролёт шёл над полюсом (наклонение ~90°)
        на высоте TARGET_PE. Здесь это стоит десятки м/с, у самой Муны — сотни.
Шаг 2. После входа в зону Муны: торможение в перицентре до круговой орбиты.
"""
import math
import time

from burn import connect, execute_node, describe_orbit

TARGET_PE = 100_000      # м, высота орбиты у Муны
TARGET_INC = 90.0        # градусов, полярная орбита
MAX_CORRECTION = 150.0   # м/с, больше не тратим на коррекцию


def arrival(node, mun):
    """(перицентр, наклонение в градусах) у Муны для данного узла, или None."""
    nxt = node.orbit.next_orbit
    if nxt is None or nxt.body.name != mun.name:
        return None
    return nxt.periapsis_altitude, math.degrees(nxt.inclination)


def cost(res):
    if res is None:
        return 1e9
    pe, inc = res
    # наклонение 90 и 270 (ретроградная полярная) одинаково хороши
    inc_err = min(abs(inc - TARGET_INC), abs(inc - (360 - TARGET_INC)))
    return ((pe - TARGET_PE) / 2000.0) ** 2 + inc_err ** 2


def plan_correction(conn, vessel):
    sc = conn.space_center
    mun = sc.bodies['Mun']
    orbit = vessel.orbit
    t_soi = orbit.time_to_soi_change
    if t_soi <= 0 or orbit.next_orbit is None or orbit.next_orbit.body.name != 'Mun':
        print('Встречи с Муной нет. Сначала mun_transfer.py.')
        return None
    ut = sc.ut + t_soi * 0.5
    node = vessel.control.add_node(ut, prograde=0, normal=0, radial=0)
    best = cost(arrival(node, mun))
    print(f'До коррекции: перицентр {arrival(node, mun)[0] / 1000:.0f} км, '
          f'наклонение {arrival(node, mun)[1]:.0f}°')

    comps = {'normal': 0.0, 'radial': 0.0, 'prograde': 0.0}
    step = 20.0
    while step >= 0.25:
        improved = False
        for name in ('normal', 'radial', 'prograde'):
            for sign in (1, -1):
                trial = dict(comps)
                trial[name] += sign * step
                total = math.sqrt(sum(v * v for v in trial.values()))
                if total > MAX_CORRECTION:
                    continue
                node.normal, node.radial, node.prograde = trial['normal'], trial['radial'], trial['prograde']
                c = cost(arrival(node, mun))
                if c < best - 1e-6:
                    best, comps, improved = c, trial, True
                    break
            node.normal, node.radial, node.prograde = comps['normal'], comps['radial'], comps['prograde']
        if not improved:
            step /= 2
    res = arrival(node, mun)
    print(f'Коррекция: dv = {node.delta_v:.1f} м/с '
          f'(норм {comps["normal"]:.1f}, рад {comps["radial"]:.1f}, прогр {comps["prograde"]:.1f}) '
          f'→ перицентр {res[0] / 1000:.0f} км, наклонение {res[1]:.0f}°')
    return node


def capture(conn, vessel):
    sc = conn.space_center
    orbit = vessel.orbit
    if orbit.body.name != 'Mun':
        print(f'Ждём входа в зону Муны ({orbit.time_to_soi_change / 60:.0f} мин)...')
        sc.warp_to(sc.ut + orbit.time_to_soi_change + 30)
        time.sleep(2)
        orbit = vessel.orbit
    if orbit.body.name != 'Mun':
        print('Аппарат не в зоне Муны, остановка.')
        return False
    describe_orbit(vessel)
    if orbit.periapsis_altitude < 15_000:
        print('Перицентр слишком низкий, есть риск врезаться. Остановка.')
        return False

    mu = orbit.body.gravitational_parameter
    rp = orbit.periapsis
    v_pe = math.sqrt(mu * (2 / rp - 1 / orbit.semi_major_axis))
    v_circ = math.sqrt(mu / rp)
    dv = v_circ - v_pe
    ut = sc.ut + orbit.time_to_periapsis
    print(f'Торможение в перицентре: {dv:.0f} м/с через {orbit.time_to_periapsis / 60:.0f} мин')
    node = vessel.control.add_node(ut, prograde=dv)
    return execute_node(conn, vessel, node)


def main():
    conn, vessel = connect('Mun capture')
    if vessel.orbit.body.name == 'Kerbin':
        node = plan_correction(conn, vessel)
        if node is None:
            return
        if node.delta_v < 0.5:
            print('Коррекция не нужна.')
            node.remove()
        elif not execute_node(conn, vessel, node):
            return
    if capture(conn, vessel):
        describe_orbit(vessel)
        print('Полярная орбита Муны готова. Сделай скрин (F1). Дальше: python mun_impact.py')


if __name__ == '__main__':
    main()

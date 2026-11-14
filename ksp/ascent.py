"""Автопилот выведения на круговую орбиту Kerbin через kRPC.

Ракета стоит на старте, сервер kRPC запущен. Запуск:
    python ascent.py
В соседнем окне можно параллельно запустить telemetry.py.

Закон тангажа тот же, что в физической модели: до TURN_START летим
вертикально, потом угол плавно уменьшается по корню до 0 на TURN_END.
"""
import math
import time

import krpc

from burn import ap_engage, point_at

TARGET_ALT = 80_000   # м, целевая высота орбиты
TURN_START = 1_000    # м, начало гравитационного разворота
TURN_END = 45_000     # м, к этой высоте ракета лежит горизонтально
HEADING = 90          # градусов, на восток (по вращению Kerbin)
ATMOSPHERE = 70_000   # м, граница атмосферы Kerbin


def pitch_for(alt):
    if alt < TURN_START:
        return 90.0
    if alt > TURN_END:
        return 0.0
    frac = (alt - TURN_START) / (TURN_END - TURN_START)
    return 90.0 * (1 - math.sqrt(frac))


def engines_burning(vessel):
    return any(e.active and e.has_fuel for e in vessel.parts.engines)


def main():
    conn = krpc.connect(name='Ascent')
    sc = conn.space_center
    vessel = sc.active_vessel
    ap = vessel.auto_pilot
    print(f'Аппарат: {vessel.name}')

    vessel.control.sas = False
    vessel.control.rcs = False
    vessel.control.throttle = 1.0
    ap.reference_frame = vessel.surface_reference_frame
    ap.target_pitch_and_heading(90, HEADING)
    ap_engage(ap, True)

    for i in (3, 2, 1):
        print(f'{i}...')
        time.sleep(1)
    print('Старт!')
    vessel.control.activate_next_stage()

    # Активный участок: разворот и сброс пустых ступеней
    empty_stagings = 0
    while vessel.orbit.apoapsis_altitude < TARGET_ALT:
        alt = vessel.flight().mean_altitude
        ap.target_pitch_and_heading(pitch_for(alt), HEADING)

        if engines_burning(vessel):
            empty_stagings = 0
        else:
            empty_stagings += 1
            if empty_stagings > 2:
                print('Нет работающих двигателей после двух отделений, проверь порядок ступеней.')
                vessel.control.throttle = 0
                return
            print(f'Отделение ступени на высоте {alt / 1000:.1f} км')
            vessel.control.activate_next_stage()
            time.sleep(1)
        time.sleep(0.05)

    print(f'Апоцентр {TARGET_ALT / 1000:.0f} км достигнут, двигатель выключен')
    vessel.control.throttle = 0.0

    # Пока в атмосфере, апоцентр проседает от сопротивления: подталкиваем
    while vessel.flight().mean_altitude < ATMOSPHERE:
        ap.target_pitch_and_heading(0, HEADING)
        if vessel.orbit.apoapsis_altitude < TARGET_ALT:
            vessel.control.throttle = 0.2
        else:
            vessel.control.throttle = 0.0
        time.sleep(0.1)
    vessel.control.throttle = 0.0

    for fairing in vessel.parts.fairings:
        fairing.jettison()
    print('Вышли из атмосферы, обтекатель сброшен')

    # Скругление в апоцентре: delta-v по формуле vis-viva
    orbit = vessel.orbit
    mu = orbit.body.gravitational_parameter
    r = orbit.apoapsis
    v_now = math.sqrt(mu * (2 / r - 1 / orbit.semi_major_axis))
    v_circ = math.sqrt(mu / r)
    dv = v_circ - v_now
    node = vessel.control.add_node(sc.ut + orbit.time_to_apoapsis, prograde=dv)

    # Время работы двигателя по формуле Циолковского
    thrust = vessel.available_thrust
    ve = vessel.specific_impulse * 9.82
    m0 = vessel.mass
    m1 = m0 / math.exp(dv / ve)
    burn_time = (m0 - m1) / (thrust / ve)
    print(f'Скругление: dv = {dv:.0f} м/с, работа двигателя {burn_time:.1f} с')

    point_at(ap, node.reference_frame, (0, 1, 0))

    burn_ut = sc.ut + orbit.time_to_apoapsis - burn_time / 2
    sc.warp_to(burn_ut - 10)
    point_at(ap, node.reference_frame, (0, 1, 0), timeout=10)
    while sc.ut < burn_ut:
        time.sleep(0.05)

    vessel.control.throttle = 1.0
    time.sleep(max(burn_time - 0.5, 0))
    vessel.control.throttle = 0.05
    while node.remaining_burn_vector(node.reference_frame)[1] > 0.5:
        time.sleep(0.02)
    vessel.control.throttle = 0.0
    node.remove()

    ap_engage(ap, False)
    vessel.control.sas = True
    o = vessel.orbit
    print(f'Орбита: Ap = {o.apoapsis_altitude / 1000:.1f} км, '
          f'Pe = {o.periapsis_altitude / 1000:.1f} км. Готово, дальше вручную.')


if __name__ == '__main__':
    main()

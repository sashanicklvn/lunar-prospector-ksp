"""Общие функции для скриптов автополёта: подключение, разворот,
выполнение узла манёвра с отделением пустых ступеней.

Используется из mun_transfer.py, mun_capture.py и mun_impact.py.
"""
import math
import time

import krpc

G0 = 9.82


def ap_engage(ap, on=True):
    """Включает/выключает автопилот. В kRPC 0.5 это ap.engage(),
    в kRPC 0.6 — свойство ap.engaged."""
    if hasattr(ap, 'engage'):
        if on:
            ap.engage()
        else:
            ap.disengage()
    else:
        ap.engaged = on


def connect(name):
    conn = krpc.connect(name=name)
    vessel = conn.space_center.active_vessel
    print(f'Аппарат: {vessel.name}, тело: {vessel.orbit.body.name}')
    return conn, vessel


def stage_until_thrust(vessel, max_stagings=3):
    """Если тяги нет (ступень пуста), отделяем ступени, пока не появится."""
    for _ in range(max_stagings):
        if vessel.available_thrust > 0:
            return True
        if vessel.control.current_stage <= 0:
            break
        print('Нет тяги, отделяем ступень')
        vessel.control.activate_next_stage()
        time.sleep(1.0)
    return vessel.available_thrust > 0


def burn_time_for(vessel, dv):
    """Время работы двигателя по формуле Циолковского."""
    thrust = vessel.available_thrust
    isp = vessel.specific_impulse
    if thrust <= 0 or isp <= 0:
        return None
    ve = isp * G0
    m0 = vessel.mass
    m1 = m0 / math.exp(abs(dv) / ve)
    return (m0 - m1) / (thrust / ve)


def point_at(ap, reference_frame, direction, timeout=90, tolerance_deg=1.5):
    """Поворачиваем аппарат и ждём, пока он успокоится (с ограничением по времени)."""
    ap.reference_frame = reference_frame
    ap.target_direction = direction
    ap_engage(ap, True)
    start = time.time()
    while time.time() - start < timeout:
        if ap.error < tolerance_deg:
            # ещё секунда, чтобы погасить вращение
            time.sleep(1.0)
            if ap.error < tolerance_deg:
                return True
        time.sleep(0.2)
    print(f'Внимание: аппарат не довернулся за {timeout} с, ошибка {ap.error:.1f}°')
    return False


def execute_node(conn, vessel, node, lead_time=20):
    """Выполняет узел манёвра: разворот, ускорение времени, разгон, точная дотяжка.

    Узел читается «вживую», поэтому его можно двигать мышкой в карте до старта.
    """
    sc = conn.space_center
    ap = vessel.auto_pilot
    vessel.control.sas = False
    vessel.control.rcs = False
    vessel.control.throttle = 0.0

    if not stage_until_thrust(vessel):
        print('Двигателя с топливом нет, манёвр невозможен.')
        return False

    dv = node.delta_v
    bt = burn_time_for(vessel, dv)
    if bt is None:
        print('Не удалось посчитать время работы двигателя.')
        return False
    print(f'Манёвр: dv = {dv:.1f} м/с, двигатель ~{bt:.0f} с, '
          f'через {node.time_to:.0f} с')

    # Разворот на узел
    point_at(ap, node.reference_frame, (0, 1, 0))

    # Ускорение времени до момента за lead_time секунд до начала разгона
    burn_start = node.ut - bt / 2
    if burn_start - sc.ut > lead_time + 5:
        print('Ускоряем время...')
        sc.warp_to(burn_start - lead_time)
    point_at(ap, node.reference_frame, (0, 1, 0), timeout=lead_time)
    while sc.ut < burn_start:
        time.sleep(0.05)

    # Основной разгон
    print('Двигатель включён')
    vessel.control.throttle = 1.0
    last_remaining = node.remaining_delta_v
    while True:
        remaining = node.remaining_delta_v
        if vessel.available_thrust <= 0:
            vessel.control.throttle = 0.0
            if not stage_until_thrust(vessel):
                print('Топливо кончилось во время манёвра.')
                return False
            # после смены ступени тяга другая: пересчитываем время
            vessel.control.throttle = 1.0
        if remaining < 0.5 or remaining > last_remaining + 0.5:
            break
        # ближе к концу снижаем тягу, чтобы не перескочить
        if remaining < 15:
            vessel.control.throttle = 0.2
        elif remaining < 40:
            vessel.control.throttle = 0.5
        last_remaining = min(last_remaining, remaining)
        time.sleep(0.05)
    vessel.control.throttle = 0.0
    print(f'Двигатель выключен, остаток {node.remaining_delta_v:.1f} м/с')
    node.remove()
    ap_engage(ap, False)
    vessel.control.sas = True
    return True


def describe_orbit(vessel):
    o = vessel.orbit
    print(f'Орбита вокруг {o.body.name}: Ap = {o.apoapsis_altitude / 1000:.1f} км, '
          f'Pe = {o.periapsis_altitude / 1000:.1f} км, '
          f'наклонение {math.degrees(o.inclination):.1f}°')

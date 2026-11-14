"""Сход с орбиты Муны и падение на поверхность (финал миссии Lunar Prospector).

Аппарат на орбите Муны, сервер kRPC запущен, telemetry.py пишет лог. Запуск:
    python mun_impact.py

Скрипт ставит узел торможения в апоцентре так, чтобы перицентр ушёл под
поверхность, и ждёт Enter: в этот момент узел можно передвинуть мышкой в карте,
чтобы точка падения попала в нужный кратер. Потом выполняет узел и доводит
аппарат до удара хвостом вперёд.
"""
import math
import time

from burn import connect, execute_node, describe_orbit, ap_engage

PE_BELOW_SURFACE = 15_000   # м, насколько опускаем перицентр под поверхность
SLOW_DOWN_ALT = 12_000      # м над поверхностью, где возвращаем обычное время


def main():
    conn, vessel = connect('Mun impact')
    sc = conn.space_center
    orbit = vessel.orbit
    if orbit.body.name != 'Mun':
        print('Аппарат не на орбите Муны.')
        return
    describe_orbit(vessel)

    mu = orbit.body.gravitational_parameter
    ra = orbit.apoapsis
    rp_new = orbit.body.equatorial_radius - PE_BELOW_SURFACE
    a_new = (ra + rp_new) / 2
    v_now = math.sqrt(mu * (2 / ra - 1 / orbit.semi_major_axis))
    v_new = math.sqrt(mu * (2 / ra - 1 / a_new))
    dv = v_new - v_now
    ut = sc.ut + orbit.time_to_apoapsis
    node = vessel.control.add_node(ut, prograde=dv)
    print(f'Узел схода с орбиты: {dv:.0f} м/с в апоцентре, через {orbit.time_to_apoapsis / 60:.0f} мин.')
    print('Если хочешь попасть в конкретный кратер, передвинь узел мышкой в карте (M),')
    print('чтобы конец линии лёг в кратер. Потом вернись сюда и нажми Enter.')
    input()

    if not execute_node(conn, vessel, node):
        return

    ap = vessel.auto_pilot
    flight = vessel.flight(vessel.orbit.body.reference_frame)
    print('Ждём сближения с поверхностью...')
    while flight.surface_altitude > SLOW_DOWN_ALT:
        if sc.rails_warp_factor == 0 and flight.surface_altitude > SLOW_DOWN_ALT * 3:
            sc.rails_warp_factor = 3
        time.sleep(0.2)
    sc.rails_warp_factor = 0

    # Хвостом вперёд, чтобы в кадре был двигатель и поверхность
    ap.reference_frame = vessel.surface_velocity_reference_frame
    ap.target_direction = (0, -1, 0)
    ap_engage(ap, True)
    print('Высота 12 км, падаем. Смотри в окно игры.')
    try:
        while True:
            print(f'высота {flight.surface_altitude:8.0f} м, скорость {flight.speed:6.0f} м/с')
            time.sleep(1.0)
    except Exception:
        print('Удар о поверхность. Миссия завершена.')


if __name__ == '__main__':
    main()

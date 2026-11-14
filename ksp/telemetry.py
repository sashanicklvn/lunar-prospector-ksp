"""Запись телеметрии полёта из KSP через kRPC в CSV-файл.

Запуск (KSP открыт, сервер kRPC запущен, ракета на старте):
    python telemetry.py                 -> файл flight_ГГГГММДД_ЧЧММСС.csv
    python telemetry.py ascent_try3.csv -> файл с заданным именем
Остановка: Ctrl+C. Если аппарат разбился (удар о Mun), скрипт закончит сам.

Скрипт только читает данные и ничего не нажимает, поэтому его можно
запускать параллельно с ручным полётом или с ascent.py.
"""
import csv
import math
import sys
import time
from datetime import datetime

import krpc

PERIOD = 0.5  # секунд реального времени между записями

FIELDS = [
    'ut', 'met', 'body', 'stage',
    'mass_kg', 'thrust_n', 'available_thrust_n', 'isp_s', 'throttle',
    'altitude_m', 'surface_altitude_m', 'latitude_deg', 'longitude_deg',
    'surface_speed', 'vertical_speed', 'horizontal_speed', 'orbital_speed',
    'pitch_deg', 'heading_deg',
    'dynamic_pressure_pa', 'atmosphere_density', 'drag_n',
    'apoapsis_alt_m', 'periapsis_alt_m', 'inclination_deg', 'eccentricity',
    'liquid_fuel', 'oxidizer',
]


def sample(sc, vessel):
    orbit = vessel.orbit
    body = orbit.body
    surf = vessel.flight(body.reference_frame)
    inert = vessel.flight(body.non_rotating_reference_frame)
    res = vessel.resources
    drag = surf.drag
    return {
        'ut': round(sc.ut, 2),
        'met': round(vessel.met, 2),
        'body': body.name,
        'stage': vessel.control.current_stage,
        'mass_kg': round(vessel.mass, 1),
        'thrust_n': round(vessel.thrust, 1),
        'available_thrust_n': round(vessel.available_thrust, 1),
        'isp_s': round(vessel.specific_impulse, 1),
        'throttle': round(vessel.control.throttle, 2),
        'altitude_m': round(surf.mean_altitude, 1),
        'surface_altitude_m': round(surf.surface_altitude, 1),
        'latitude_deg': round(surf.latitude, 4),
        'longitude_deg': round(surf.longitude, 4),
        'surface_speed': round(surf.speed, 2),
        'vertical_speed': round(surf.vertical_speed, 2),
        'horizontal_speed': round(surf.horizontal_speed, 2),
        'orbital_speed': round(inert.speed, 2),
        'pitch_deg': round(surf.pitch, 2),
        'heading_deg': round(surf.heading, 2),
        'dynamic_pressure_pa': round(surf.dynamic_pressure, 1),
        'atmosphere_density': round(surf.atmosphere_density, 5),
        'drag_n': round(math.sqrt(sum(c * c for c in drag)), 1),
        'apoapsis_alt_m': round(orbit.apoapsis_altitude, 1),
        'periapsis_alt_m': round(orbit.periapsis_altitude, 1),
        'inclination_deg': round(math.degrees(orbit.inclination), 3),
        'eccentricity': round(orbit.eccentricity, 5),
        'liquid_fuel': round(res.amount('LiquidFuel'), 2),
        'oxidizer': round(res.amount('Oxidizer'), 2),
    }


def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = datetime.now().strftime('flight_%Y%m%d_%H%M%S.csv')

    conn = krpc.connect(name='Telemetry')
    sc = conn.space_center
    print(f'Подключено к KSP, аппарат: {sc.active_vessel.name}')
    print(f'Пишу в {filename}. Остановить: Ctrl+C')

    last_ut = None
    last_body = None
    last_print = 0.0
    rows = 0
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        try:
            while True:
                try:
                    row = sample(sc, sc.active_vessel)
                except (krpc.error.RPCError, ValueError) as e:
                    # аппарат уничтожен или вышли из полёта в меню
                    print(f'Аппарат недоступен ({e}). Запись закончена.')
                    break

                # на паузе и в меню время не идёт, такие строки не пишем
                if row['ut'] != last_ut:
                    writer.writerow(row)
                    f.flush()
                    rows += 1
                    last_ut = row['ut']

                if row['body'] != last_body:
                    print(f"T+{row['met']:.0f} с: теперь у тела {row['body']}")
                    last_body = row['body']

                if time.time() - last_print > 5:
                    print(f"T+{row['met']:8.0f} с  h={row['altitude_m'] / 1000:8.1f} км  "
                          f"v={row['orbital_speed']:7.0f} м/с  "
                          f"Ap={row['apoapsis_alt_m'] / 1000:8.1f} км  "
                          f"Pe={row['periapsis_alt_m'] / 1000:8.1f} км")
                    last_print = time.time()

                time.sleep(PERIOD)
        except KeyboardInterrupt:
            print('Остановлено вручную.')
    print(f'Записано строк: {rows}, файл: {filename}')


if __name__ == '__main__':
    main()

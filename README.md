<div align="center">

<img src="https://nssdc.gsfc.nasa.gov/image/spacecraft/lunarprosp.gif" width="260" alt="Lunar Prospector">

# Lunar Prospector в KSP

**Моделирование лунной миссии NASA 1998 года в Kerbal Space Program**

</div>

## О проекте

**Lunar Prospector** — станция NASA, которая в 1998–1999 годах изучала Луну с полярной орбиты и нашла признаки водяного льда у полюсов. В конце миссии её направили в кратер у южного полюса.

Мы повторяем эту миссию в Kerbal Space Program и сравниваем полёт в игре с собственной физико-математической моделью на Python.

## Миссия в KSP

**Старт с Кербина** → **орбита Кербина 80 км** → **перелёт к Муне** → **полярная орбита** → **падение у южного полюса**

Весь полёт выполняют скрипты на Python через мод kRPC.

### Что получилось

| Параметр | Результат |
|---|---|
| Орбита Кербина | 80 × 79 км |
| Полярная орбита Муны | 100 × 100 км, наклонение 89,7° |
| Место падения | 82° ю. ш., примерно 28 км от южного полюса |
| Скорость удара | около 606 м/с |

Видео полёта: (https://disk.yandex.ru/d/UhvIzO7oRGsEaQ)

### Графики

![Выведение](flight/grafik_1_vyvedenie.png)
![Перелёт](flight/grafik_2_perelet.png)
![Орбиты](flight/grafik_3_orbity.png)
![Падение](flight/grafik_4_padenie.png)

### Кадры полёта

| | |
|---|---|
| ![](screenshots/01_start_s_kerbina.png) Старт | ![](screenshots/04_orbita_kerbina.png) Орбита Кербина |
| ![](screenshots/06_traektoriya_pereleta.png) Перелёт к Муне | ![](screenshots/10_polyarnaya_orbita_muny.png) Полярная орбита Муны |
| ![](screenshots/12_padenie_k_yuzhnomu_polyusu.png) Падение | ![](screenshots/14_itog_poleta.png) Итог полёта |

Остальные кадры лежат в папке [screenshots](screenshots).

## Что лежит в репозитории

| Папка / файл | Что это |
|---|---|
| [docs/research.md](docs/research.md) | ресерч-док: реальная миссия, физика полёта, формулы, расчёт ΔV, источники |
| [ksp/](ksp) | скрипты полёта: взлёт, перелёт, торможение, падение, запись телеметрии |
| [flight/final3.csv](flight/final3.csv) | телеметрия итогового полёта |
| [flight/plot_flight_v2.py](flight/plot_flight_v2.py) | скрипт, который строит графики по телеметрии |
| [screenshots/](screenshots) | кадры этапов полёта |
| [craft/lunar_prospector.craft](craft/lunar_prospector.craft) | файл ракеты из KSP |


## Команда «Lunar Prospector»

Группа М8О-114БВ-26

| Участник | Роль |
|---|---|
| Родионова Александра | тимлид · KSP · медиа |
| Порфирьева Полина | физик-математик |
| Доронина Евгения | программист |

## Источники

[NASA NSSDCA](https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=1998-001A) · [NASA Science](https://science.nasa.gov/mission/lunar-prospector/) · [Lunar Prospector Mission Handbook, 1998](https://pds-geosciences.wustl.edu/missions/lunarp/schandbk.pdf)

Полный список в [ресерч-доке](docs/research.md).

---

<sub>Проект по дисциплине «Введение в авиационную и ракетно-космическую технику», МАИ, 2026</sub>

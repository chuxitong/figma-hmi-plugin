# Сводка по полному прогону экспериментов

Модель: `rule-based-v0.1`  
Триалов на фазу: 3  
Итераций уточнения: 2  
Старт: 2026-04-17T20:43:53  
Финиш: 2026-04-17T20:44:19  

## Средние тайминги (секунды)

| Мокап | Сложность | Generate | Refine 1 | Refine 2 | Edit |
| --- | --- | ---: | ---: | ---: | ---: |
| m1_equipment_status | simple | 0.0505 | 0.0504 | 0.0504 | 0.0506 |
| m2_alarm_event | simple | 0.0504 | 0.0504 | 0.0503 | 0.0506 |
| m3_trend_monitor | medium | 0.0503 | 0.0505 | 0.0504 | 0.0504 |
| m4_operator_panel | medium | 0.0502 | 0.0503 | 0.0503 | 0.0501 |
| m5_production_overview | medium | 0.0505 | 0.0505 | 0.0504 | 0.0506 |
| m6_tank_synoptic | medium-hard | 0.0504 | 0.0506 | 0.0503 | 0.0502 |
| m7_energy_dashboard | medium-hard | 0.0503 | 0.0504 | 0.0504 | 0.0505 |
| m8_batch_recipe | hard | 0.0502 | 0.0504 | 0.0502 | 0.0503 |

## Примечания
В таблице — время только вызова модели (или её заместителя); рендер HTML→PNG через Playwright считается отдельно.
В каждой папке `baseline-tests/outputs/full-eval/<mockup>/` лежит пара HTML+PNG для фаз `generate`, `refine_iter1`, `refine_iter2`, `edit`.
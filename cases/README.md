# `cases/` — банк учебных задач (Mentor)

JSONL-файлы с задачами для прогона системы (см. `docs/TESTING_AND_MENTOR.md` §3).
Каждая задача размечена: домен, сложность, ожидаемый `proof_level` и — где возможно —
эталон из надёжного источника (учебник/CODATA/аналитика).

Наполняется начиная с Этапа M (Mentor).

## Сид-корпус

| Файл | Кейсы |
|------|--------|
| `physics/apple_weight.jsonl` | `apple_weight` (аналитика F=mg), `falling_ode` (метаморфный) |

Запуск: `dbse-mentor run --cases cases --verdicts verdicts` — вердикты пишутся в
`verdicts/YYYY-MM-DD.jsonl` (каталог в `.gitignore`).

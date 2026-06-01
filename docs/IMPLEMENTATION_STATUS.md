# Статус реализации ROADMAP (MVP)

> Обновлено при закрытии этапов 0–12 и M по планам `docs/superpowers/plans/`.
> **Источник истины по коду:** `README.md` (раздел «Статус»), **по тестам:** `pytest`.

## Этапы 0–12 + M — реализовано (MVP)

| Этап | Слой / область | Пакет / точка входа | QA |
|------|----------------|---------------------|-----|
| 0 | Каркас, контракты, пайплайн | `dbse/contracts`, `dbse/pipeline` | skeleton + CI |
| 1 | L1 Dimensions | `dbse/dimensional/` | 1, 2 |
| 2 | L1.5 Affine | `dbse/semantic/` | 1, 2, 5 |
| 3 | L0 + L0.5 | `dbse/membrane/`, `dbse/sts/`, слои | 1, 5, 7 (parse corpus) |
| 4 | L3 RIBOSOME | `dbse/ribosome/`, слой | 1, 2, 5 |
| 5 | L4 CYTOPLASM | `dbse/cytoplasm/`, слой | 1, 4 |
| 6 | L5 NUCLEUS (алгебра) | `dbse/nucleus/` | 1, 3, 4 |
| 7 | L5 NUCLEUS (ОДУ+Z3) | `dbse/nucleus/` | 1, 3, 4, 5 |
| 8 | L2 Model Lattice | `dbse/lattice/`, слой | 1, 5 |
| 9 | L6 Narrative | `dbse/narrative/`, слой | 1, 2 |
| 10 | L7 Expression | `dbse/expression/`, слой | 1, 5 |
| 11 | Core / Hypothesis | `dbse/knowledge/`, guard в L4 | 1, 5 |
| 12 | Production API | `dbse/api/`, `dbse-api` | 1, 6 (contract tests) |
| M | Mentor CLI | `dbse/mentor/`, `dbse-mentor run` | 1, core guard |

**E2E DoD:** `tests/test_e2e_dod.py` — эталонный запрос про яблоко 100 г через весь пайплайн.

## Намеренно pass-through (не «незавершено»)

- `dbse/layers/dimensional.py`, `dbse/layers/affine_types.py` — ранний pruning в
  `dbse/ribosome/compile` (`parse_unit`, `affine()`). См. `docs/spec-notes.md` §L3.

## Отложено (вне MVP текущих планов)

| Область | ROADMAP / ТЗ | Примечание |
|---------|--------------|------------|
| OpenTelemetry, rate limiting | Этап 12 | только FastAPI + Mermaid + contract tests |
| `schemathesis` | QA ур. 6 | ручные contract tests в `tests/api/` |
| LLM styling (L7) | Этап 10 | `style_fallback` + валидатор; LLM — позже |
| Mentor `triage` / `promote` / `report` | Этап M (ROADMAP) | в плане только `run` |
| Этап 13+ | новые плагины, IDE, тензоры | вне scope планов 2026-05-31 |

## Порядок планов (выполнен)

```
6 → 7 → 9 → 10 → 11 → 12 → M
      ↘ 8 (после 3)
```

Этапы 1–5 реализованы до этапов 6–7 (исторически на ветке).

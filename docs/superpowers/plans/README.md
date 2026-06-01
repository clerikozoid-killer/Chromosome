# Superpowers — индекс планов реализации

> **Выполнение:** superpowers:subagent-driven-development — свежий субагент на задачу, двухэтапное ревью (spec → quality) между задачами.
>
> Команда `/write-plan` **устарела** — используйте skill **writing-plans**.
>
> **Код:** этапы 0–12 и M закрыты (MVP). Сводка: [`docs/IMPLEMENTATION_STATUS.md`](../../IMPLEMENTATION_STATUS.md).

## Планы по этапам ROADMAP

| Этап | Слой | Файл плана | План | Код (MVP) |
|------|------|------------|------|-----------|
| 1 | L1 Dimensions | [2026-05-31-l1-dimensional-analysis.md](2026-05-31-l1-dimensional-analysis.md) | ✅ | ✅ |
| 2 | L1.5 Affine Types | [2026-05-31-l1_5-affine-types.md](2026-05-31-l1_5-affine-types.md) | ✅ | ✅ |
| 3 | L0 + L0.5 | [2026-05-31-l0-membrane-l0_5-sts-typing.md](2026-05-31-l0-membrane-l0_5-sts-typing.md) | ✅ | ✅ |
| 4 | L3 RIBOSOME | [2026-05-31-l3-ribosome-ast-hash-cache.md](2026-05-31-l3-ribosome-ast-hash-cache.md) | ✅ | ✅ |
| 5 | L4 CYTOPLASM | [2026-05-31-l4-cytoplasm-domain-plugins.md](2026-05-31-l4-cytoplasm-domain-plugins.md) | ✅ | ✅ |
| 6 | L5 NUCLEUS (алгебра) | [2026-05-31-l5-nucleus-algebra-sympy-proof-tinfo.md](2026-05-31-l5-nucleus-algebra-sympy-proof-tinfo.md) | ✅ | ✅ |
| 7 | L5 NUCLEUS (ОДУ+Z3) | [2026-05-31-l5-nucleus-ode-monitor-z3-budgets.md](2026-05-31-l5-nucleus-ode-monitor-z3-budgets.md) | ✅ | ✅ |
| 8 | L2 Model Lattice | [2026-05-31-l2-context-model-lattice.md](2026-05-31-l2-context-model-lattice.md) | ✅ | ✅ |
| 9 | L6 Narrative | [2026-05-31-l6-semantic-narrative-graph.md](2026-05-31-l6-semantic-narrative-graph.md) | ✅ | ✅ |
| 10 | L7 Expression | [2026-05-31-l7-expression-constrained-styling.md](2026-05-31-l7-expression-constrained-styling.md) | ✅ | ✅ |
| 11 | Core / Hypothesis | [2026-05-31-core-hypothesis-layer.md](2026-05-31-core-hypothesis-layer.md) | ✅ | ✅ |
| 12 | Production API | [2026-05-31-production-api-observability.md](2026-05-31-production-api-observability.md) | ✅ | ✅ |
| M | Mentor CLI | [2026-05-31-mentor-cli.md](2026-05-31-mentor-cli.md) | ✅ | ✅ |

Этап 0 — базовый каркас репозитория (`ROADMAP.md` §Этап 0), отдельного plan-файла нет.

Этап 13+ (новые плагины, тензоры, IDE) — вне текущего scope.

## Порядок выполнения

```
6 → 7 → 9 → 10 → 11 → 12 → M
      ↘ 8 (параллельно после 3)
```

## Subagent-Driven workflow

1. Прочитать plan один раз → TodoWrite по всем задачам.
2. На задачу: implementer subagent с **полным текстом задачи** (не заставлять читать файл плана).
3. Spec review → quality review → отметить выполненной.
4. После последней задачи: final reviewer + **finishing-a-development-branch**.

## Закрываемые уязвимости

| Этап | Уязвимость |
|------|------------|
| 7 | ODE Drift (#3), Z3 explosion (#5) |
| 8 | Контекстная неоднозначность |
| 9–10 | ELI5 hallucinations (#4) |
| 11 | CRISPR на аксиомы (#7) |

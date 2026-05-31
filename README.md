# DBSE v5.0 «Chromosome»

Детерминированный физико-математический «компилятор реальности».
LLM — только периферия (вход: парсинг, выход: стилизация). Вся истина — в символьных
движках и строгой системе типов. Цель — **ноль галлюцинаций в ядре**.

## Документация

- [`DBSE v5.0 «Chromosome».txt`](DBSE%20v5.0%20%C2%ABChromosome%C2%BB.txt) — источник истины (спецификация).
- [`ROADMAP.md`](ROADMAP.md) — поэтапный план реализации (послойное углубление).
- [`docs/TESTING_AND_MENTOR.md`](docs/TESTING_AND_MENTOR.md) — стратегия тестирования и сопровождения.
- [`docs/spec-notes.md`](docs/spec-notes.md) — заметки/расхождения и консолидация RFC.

## Архитектура (пайплайн)

```
L0  MEMBRANE        (LLM parser, sandbox)
L0.5 STS TYPING     (rule-based классификатор)
L1  DIMENSIONS      ([M, L, T, I, Θ, N, J])
L1.5 AFFINE TYPES   (Dimension + SemanticTag + rank + frame)
L2  MODEL LATTICE   (P(Model | Context), T_ambig)
L3  RIBOSOME        (AST compiler + canonical hash + cache)
L4  CYTOPLASM       (epigenetics + domain plugins)
L5  NUCLEUS         (SymPy/Z3 + Continuous Invariant Monitor)
L6  NARRATIVE       (semantic narrative graph, шаблоны)
L7  EXPRESSION      (constrained LLM styling)
```

## Статус

- Этап 0 — фундамент: ✅ каркас, контракты, заглушки, QA-инфра.
- Этап 1 — L1 (размерностный анализ): ✅ парсинг единиц + правила размерностей
  (`dbse/dimensional/`). Интеграция в слой `L1.DIMENSIONS` — после L0 (Этап 3).
- Этап 2 — L1.5 (affine types): ✅ семантические теги + правила совместимости
  (`dbse/semantic/`). `compatible()`/`check_compatible()` навешивают семантику
  поверх L1-pruning (`check_add`/`check_subtract`). Интеграция в слой
  `L1.5.AFFINE_TYPES` — после L0 (Этап 3).
- Этап 3 — L0 MEMBRANE + L0.5 STS Typing: ✅ строгая Pydantic-схема выхода
  (`dbse/membrane/`, `extra="forbid"`, валидация ссылок и единиц через L1
  `parse_unit`), детерминированный fallback-парсер, провайдер-агностичный
  `ParserAdapter`; rule-based классификатор запросов (`dbse/sts/`). Слои
  `L0.MEMBRANE`/`L0.5.STS_TYPING` подключены: схема-violation → `CLARIFICATION`,
  `OPINION` → `UNHANDLED`. **Закрывает уязвимость №2 (Prompt Injection).**
- Этап 4 — L3 RIBOSOME: ✅ компиляция MEMBRANE → AST с навешиванием
  `AffineType` (L1/L1.5 в `compile`), нормализация (rename/sort/fold),
  `classify_structure`, `canonical_hash` (16 hex), подписанный LRU-кэш
  (`dbse/ribosome/`). Слой `L3.RIBOSOME` подключён: cache hit →
  `ctx.solution` без NUCLEUS. **Закрывает уязвимости №8 (Graph isomorphism
  DDoS) и №9 (Cache poisoning).**
- Этап 5 — L4 CYTOPLASM: ✅ Domain Plugin API (`DomainPlugin` Protocol),
  stdlib `PluginRegistry` (pluggy-стиль без зависимости), плагины
  `classical_mechanics` (инварианты `v<c`, выбор linear/quadratic friction)
  и каркас `fluid_mechanics` (Re/Ma/Fr → model). Слой `L4.CYTOPLASM`
  читает `config.domain_hint`, пишет `constraints`/`invariants`/`domain_model`
  для NUCLEUS (Этап 7). Плагины подключаются/отключаются без изменения ядра.
- Этап 6 — L5 NUCLEUS (часть 1): ✅ алгебраический SymPy-решатель (`F = m * g`),
  `Proof`/`ProofLevel`, `compute_tinfo`, `numeric_steps` (`dbse/nucleus/`).
  Слой `L5.NUCLEUS` подключён: cache miss → solve + cache store.
  **QA:** уровни 1 + 3 (differential) + 4 (metamorphic).
- Этап 7 — L5 NUCLEUS (часть 2): ✅ ОДУ первого порядка (SciPy + SymPy oracle),
  Continuous Invariant Monitor (`v<c` → P3 MODEL_BREAKDOWN), Z3 с бюджетом 100 мс
  (fallback P2). **Закрывает уязвимости №3 (ODE Drift) и №5 (Z3 explosion).**
- Этап 8 — L2 MODEL LATTICE: ✅ rule-based `P(Model|Context)`, `T_ambig = H/log(N)`,
  пороги `<0.3` / `0.3–0.6` / `≥0.6` → `AMBIGUITY_HALT` (`dbse/lattice/`).
  **Закрывает уязвимость контекстной неоднозначности.** **QA:** уровни 1 + 5.

## Разработка

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

ruff check .
mypy
pytest
```

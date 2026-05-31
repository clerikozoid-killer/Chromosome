# Заметки по спецификации и консолидация RFC

## Источник истины
`DBSE v5.0 «Chromosome».txt` — финальная консолидированная спецификация (v5.0). Все
реализационные решения сверяются с ней. Это единственный источник: более ранние
донорские материалы (RFC/`.docx`) в репозитории не хранятся.

## Открытые вопросы (накапливаются по ходу)
- L1 parser: голые целые в позиции фактора отвергаются (валиден только литерал `1`,
  напр. в `1/s`); это сделано осознанно, чтобы опечатки вида `m3` (вместо `m^3`) не
  проходили молча. См. `dbse/dimensional/parser.py`.

## L1.5 (Stage 2) — принятые решения
- `compatible()`/`check_compatible()` для ADD/SUB вызывают L1 `check_add`/
  `check_subtract` для размерностного гейта и лишь *добавляют* проверку
  `semantic_tag` + `tensor_rank` — логика не дублируется (см. финальный ревью L1).
  Следствие: `Energy + Force` → `DimensionError` (L1), `Energy + Torque` →
  `SemanticTypeError` (L1.5), `Work + Heat` → `InternalEnergy` (whitelist).
- Неоднозначный результат `×` (напр. `Force × Length`) кодируется прямо в
  `semantic_tag` как отсортированная строка через `|` (`"Torque|Work"`), т.к.
  контракт `AffineType` заморожен (`semantic_tag: str`). Разрешает L2 (Этап 8).
  Хелперы: `ambiguous_tag()`, `is_ambiguous()`. Инвариант «ни один тег реестра не
  содержит `|`» закреплён тестом.
- `frame_of_reference` пока НЕ участвует в проверке ADD/SUB (спецификация v5.0
  `compatible()` для ADD/SUB сверяет только dimension + semantic_tag + tensor_rank).
  Сложение векторов в разных кадрах — отложено до тензорного/релятивистского этапа
  (ROADMAP 13+). `combine()` (×/÷) кадр операндов намеренно отбрасывает.
- `combine()` (×/÷) всегда совместим (по спеку): даёт размерность по алгебре
  `Dimension` и best-effort тег (правило → тег; несколько кандидатов → ambiguous;
  нет правила → `"Unknown"`). Ранг разрешённого тега берётся из реестра; для
  ambiguous/Unknown — операндная эвристика.
- `Operator` живёт в `dbse/semantic/operators.py` (переиспользуется L3 на Этапе 4).
- Слой `dbse/layers/affine_types.py` остаётся pass-through до Этапа 3 (как
  `dbse/layers/dimensional.py` на Этапе 1).

## L0 / L0.5 (Stage 3) — принятые решения
- **Pydantic v2** — первая runtime-зависимость (спека §2/§6 требует строгую
  Pydantic-схему). Добавлен `pydantic.mypy` plugin (strict mypy). До этого
  `dependencies = []`.
- **Схема — граница песочницы.** `extra="forbid"` на всех моделях ⇒ LLM не может
  сгенерировать `INVARIANT`/`CONTEXT`/`OPERATOR` или любое off-schema поле;
  `question_type` — закрытый enum; единицы валидируются через L1 `parse_unit`
  (переиспользование, не дублирование); ссылки (`ref`/`from`/`to`/`target.ref`)
  обязаны резолвиться в объявленный `OBJECT`. Любой выход за схему →
  `MembraneError` → слой `halt(CLARIFICATION)` (никакого «молчаливого
  дополнения»).
- **Детерминированный fallback-парсер** прогоняет все тесты (без сети/LLM).
  Реальный LLM-провайдер — вне Stage 3; зашит только seam `ParserAdapter` +
  детерминированная реализация. Парсер не бросает на обычном NL: вытаскивает
  `value+unit` (единицы — через L1), отбрасывает нерезолвимое, всегда отдаёт
  схема-валидный минимум (один `obj_1`).
- **Routing** (`dbse/sts/ROUTES`) пока только записывается в trace и обрабатывает
  `OPINION → UNHANDLED`; реальный пропуск слоёв по маршруту — позже (downstream-
  слои ещё заглушки). Порядок маркеров классификатора: OPINION → DEFINITION →
  MATH_PROVE → PHYSICS_COMPUTE → AMBIGUOUS.
- **Scope:** интеграция L1/L1.5 (навешивание `AffineType` на узлы AST) — Этап 4
  (RIBOSOME), не здесь. `dbse/layers/{dimensional,affine_types}.py` остаются
  pass-through. Кириллические единицы (`г`, `м`) пока не резолвятся в L1 — это
  существующий тех-долг L1, поэтому такие величины fallback-парсер отбрасывает.
- **QA-гейт:** уровни 1 (юнит: schema/adapter/layer/classifier), 5 (adversarial:
  prompt injection — `tests/membrane/test_adversarial.py`), 7 (parsing accuracy —
  детерминированный стенд `tests/membrane/test_parse_accuracy.py` + корпус
  `cases/parse/membrane_parse.jsonl`; реальный LLM-eval — мягкий гейт, позже).

## L3 (Stage 4) — принятые решения
- **MEMBRANE расширена полем `equations: list[LinearOde1]`** — LLM по-прежнему
  не генерирует `OPERATOR`; только структурированные коэффициенты
  `d(state)/dt = constant + linear_coeff * state`. RIBOSOME строит дерево
  `DERIV`/`EQ`/`ADD`/`MUL` детерминированно.
- **L1/L1.5 интеграция в `compile`, не в layer stubs.** `quantity_affine()`
  вызывает L1 `parse_unit` + L1.5 `affine()`. Слои `L1.DIMENSIONS` /
  `L1.5.AFFINE_TYPES` остаются pass-through.
- **MVP hash — структурный, не полный изоморфизм.** Переименование переменных и
  перестановка коммутативных операндов не меняют хеш; разные коэффициенты —
  меняют. `classify_structure` для DoD: `LinearODE_Order1` покрывает и
  `dv/dt=g-kv`, и RC `dV/dt=-V/RC`.
- **Кэш:** HMAC-SHA256 подпись записи, TTL, LRU, инвалидация по `core_version`
  (хук для Этапа 11). Отравленная запись → `get()` возвращает `None` и удаляет
  ключ.
- **QA-гейт:** уровни 1 (юнит), 2 (`test_properties.py`), 5
  (`test_adversarial.py` cache poisoning).

## L4 (Stage 5) — принятые решения
- **`DomainPlugin` Protocol** в `dbse/cytoplasm/plugin.py`: шесть хуков
  (`compute_indicators`, `select_model`, `inject_constraints`,
  `register_affine_types`, `register_invariants`) + `dimensionless_numbers`.
- **Registry без pluggy** — `PluginRegistry` с явным порядком регистрации и
  per-plugin error isolation (`CytoplasmError` → trace, не crash пайплайна).
- **Domain hint только из `ctx.config`** (API `context.domain_hint`), не из
  MEMBRANE — сохраняем sandbox Stage 3 (LLM не эмитит `CONTEXT`).
- **Инварианты — data-only** на этом этапе; Continuous Invariant Monitor
  (SymPy/Z3) — Этап 7. `classical_mechanics` инъецирует `v_lt_c` (CRITICAL) и
  `energy_conserved` (SOFT).
- **Friction selection:** `drag_regime = |v|/v_ref` (default `v_ref=1 m/s`);
  `≤1` → `linear_friction`, `>1` → `quadratic_friction`.
- **`fluid_mechanics`** — reference skeleton по спеке (Re>2300 turbulent,
  Ma>0.3 compressible); не блокирует MVP.
- **QA-гейт:** уровни 1 (юнит + layer) + 4 (`test_metamorphic.py` — стабильность
  model selection при смене единиц индикаторов).

## L5 (Stage 6) — принятые решения
- **SymPy — первая научная runtime-зависимость.** Z3, ODE, Continuous Invariant
  Monitor — Этап 7.
- **MVP algebraic = recipe dispatch.** Первый рецепт: `target.force` + `mass` →
  `F = m * g` (`dbse/nucleus/recipes/weight.py`). SymPy для символики и подстановки.
- **ODE (`LinearODE_Order1`) — pass-through** с trace `skipped:ode-deferred-stage7`.
- **P0/P1 недостижимы без Z3.** `required_proof_level` P0/P1 → tag
  `domain_switch:z3-deferred-stage7` в `solver_path`, повышение `tinfo`.
- **`compute_tinfo`** в `dbse/nucleus/tinfo.py` — веса по префиксам `solver_path`
  (spec §3). Чистый алгебраический solve → `P2`, `tinfo < 0.2`.
- **Cache write on miss** — NUCLEUS кладёт результат в `SemanticCache` по
  `canonical_hash` (согласовано с RIBOSOME Stage 4).
- **Инварианты Cytoplasm** пока только в trace (`invariants_pending`); runtime
  monitor — Этап 7.
- **Конвертация массы** `g` → `kg` в `membrane_quantities_si` (тех-долг L1
  кириллических единиц не затрагиваем).
- **QA-гейт:** уровни 1 (юнит + layer), 3 (`test_differential.py`), 4
  (`test_metamorphic.py`).

## L5 (Stage 7) — принятые решения
- **ОДУ MVP:** только `LinearODE_Order1`; SciPy `solve_ivp` + event при нарушении CRITICAL.
- **Monitor:** `ContinuousInvariantMonitor.check_invariants(t, state)` на каждом шаге.
- **P3:** `HaltReason.MODEL_BREAKDOWN` + suggestion про релятивистскую модель.
- **Z3:** `z3-solver`, budget default 100 ms; timeout → `domain_switch:z3-timeout`, P2.
- **SciPy** — runtime dependency (не только dev).
- **QA:** уровни 1 + 3 (ODE differential) + 4 (k→0) + 5 (adversarial v>c).

## Технический долг L1 (из финального ревью, отложено — не блокирует Stage 2)
- Парсер мягок к «битым» операторам: `"m*"`, `"/s"`, `"m**s"` не отвергаются.
  Решить при ужесточении грамматики (нужно ли вообще, или это out-of-scope для unit-строк).
- `parser.py`: docstring грамматики слегка устарел после фикса (литерал `1` как фактор) —
  актуализировать при следующем касании файла.
- `units.resolve`: `sorted(_PREFIXES, ...)` считается на каждый вызов — вынести в константу.
- Дробные степени единиц (`m^0.5`) не парсятся, хотя `Dimension` поддерживает корни
  (Fraction). Добавить, когда появится реальная потребность.
- Stage 2 (L1.5): `check_add`/`check_subtract` должны остаться общим размерностным
  pruning'ом, поверх которого `compatible()` добавляет семантические теги — не дублировать.

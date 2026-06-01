# DBSE v5.0 «Chromosome»

Детерминированный физико-математический «компилятор реальности»: текстовый запрос
проходит через слои L0→L7, на выходе — численный ответ, уровень доказательности,
скелет объяснения и (опционально) стилизованный текст. LLM в MVP **не обязателен**
— вход парсится детерминированным fallback-парсером, выход стилизуется шаблоном.

Репозиторий: [github.com/clerikozoid-killer/Chromosome](https://github.com/clerikozoid-killer/Chromosome)

---

## Что это простыми словами

**Chromosome** — не чат-бот «на все темы», а **конвейер для физико-математических задач**:

1. Вы задаёте вопрос текстом.
2. Система **разбирает** его (масса, сила, что искать).
3. **Считает** ответ формулами (SymPy, SciPy, при необходимости Z3).
4. **Проверяет** здравый смысл (размерности, аксиомы, инварианты вроде «v < c»).
5. **Объясняет** результат шаблонами (без обязательного LLM в текущей версии).

Ответ сопровождается **уровнем доверия** (`proof`, `tinfo`): насколько выводу можно верить
в рамках выбранной модели.

**ROADMAP.md** — план разработки («что хотели построить»). **README** — как установить
и пользоваться. **Спека** `DBSE v5.0 «Chromosome».txt` — целевой идеал; в коде сейчас **MVP**
(см. `[docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md)`).

### Для чего применять


| Задача                                                     | Подходит?                      |
| ---------------------------------------------------------- | ------------------------------ |
| Учебная задача: сила, масса, падение, простая ОДУ          | Да, с `domain_hint`            |
| API/сервис «решить задачу по JSON»                         | Да (`dbse-api`)                |
| Отсечь абсурд (Energy + Torque, F=ma² в Core)              | Да, на уровне библиотек/тестов |
| Уточнить двусмысленный вопрос («яблоко» = цена или фрукт?) | Да (L2)                        |
| Общие мнения, история, программирование, химия без плагина | Нет                            |


---

## Что уже сделано (MVP)


| Часть              | Назначение                                                                       |
| ------------------ | -------------------------------------------------------------------------------- |
| **Пайплайн L0–L7** | От парсинга запроса до `solution` + `proof` + narrative + expression             |
| **L5 NUCLEUS**     | SymPy (например `F = m·g`), ОДУ 1-го порядка, монитор инвариантов, Z3 с бюджетом |
| **L4 плагины**     | `classical_mechanics`, каркас `fluid_mechanics`                                  |
| **L2**             | Неоднозначные запросы → `AMBIGUITY_HALT` + кандидаты                             |
| **Core**           | Замороженные аксиомы; атаки вида `F = m·a²` отклоняются                          |
| **API**            | `POST /api/v5/solve`, `POST /api/v5/clarify`                                     |
| **Mentor**         | Прогон банка задач `cases/**/*.jsonl` → отчёт в `verdicts/`                      |


Подробная таблица этапов: `[docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md)`.

---

## Установка (пример)

### Вариант A — клон с GitHub (рекомендуется)

```powershell
# куда угодно, в любую папку:
cd <ваша_папка>
git clone https://github.com/clerikozoid-killer/Chromosome.git
cd Chromosome

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Проверка:

```powershell
pytest
python -c "from dbse.pipeline import Pipeline; print('OK')"
```

### Вариант В — уже скачали ZIP / скопировали папку

```powershell
cd ПУТЬ\К\ПАПКЕ\Chromosome   # здесь должны быть pyproject.toml и dbse/
pip install -e ".[dev]"
```

Требования: **Python 3.11+** (3.12 тоже подходит). На Windows удобнее PowerShell;
в активированном venv команды `dbse-api` и `dbse-mentor` появятся после установки.

---

## Как пользоваться

### 1. Python — один запрос через весь пайплайн

```python
from dbse.pipeline import Pipeline

ctx = Pipeline().run(
    "С какой силой Земля притягивает яблоко массой 100г?",
    config={"domain_hint": "classical_mechanics"},
)

print("halted:", ctx.halted, ctx.halt_reason)
print("solution:", ctx.solution)   # value, unit, symbolic, numeric_steps
print("proof:", ctx.proof)         # level, tinfo, confidence
print("narrative:", ctx.narrative.get("skeleton") if ctx.narrative else None)
print("expression:", ctx.expression)  # eli5 / academic / business
```

Для задач с силой/массой указывайте `"domain_hint": "classical_mechanics"` —
иначе L4 не подключит плагин Ньютона. Единица `100г` поддерживается (кириллица
в токене единицы); без пробела после числа тоже: `100г`.

### 2. HTTP API

После `pip install -e ".[dev]"`:

```powershell
dbse-api
# сервер: http://127.0.0.1:8000
# документация: http://127.0.0.1:8000/docs
```

Пример (PowerShell):

```powershell
$body = @{
  query = "С какой силой Земля притягивает яблоко массой 100г?"
  context = @{ domain_hint = "classical_mechanics" }
  required_proof_level = "P2"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v5/solve" `
  -ContentType "application/json" -Body $body
```

Неоднозначный запрос (уточнение):

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v5/clarify" `
  -ContentType "application/json" -Body '{"query":"Сколько стоит яблоко?"}'
```

### 3. Mentor — банк учебных задач

Из **корня репозитория** (нужны каталоги `cases/` и `verdicts/`):

```powershell
dbse-mentor run --cases cases --verdicts verdicts
# вывод: 2/2 passed (или 1/2 — см. кейс falling_ode)
# файл: verdicts\YYYY-MM-DD.jsonl
```

### 4. Тесты и качество (разработчикам)

```powershell
ruff check .
mypy
pytest
```

E2E по эталону ТЗ: `tests/test_e2e_dod.py`.

---

## Эталонные сценарии (10 из спеки — что реально есть в MVP)

Ниже — ваши 10 сценариев с **честной** привязкой к коду. Статусы:


| Статус | Значение                                                                         |
| ------ | -------------------------------------------------------------------------------- |
| ✅      | Поведение есть; можно воспроизвести командами ниже                               |
| ⚠️     | Идея верная, в MVP упрощено или только через тесты/API, не из «красивого» текста |
| ❌      | В полной спеке, в репозитории **пока нет**                                       |



| №   | Сценарий                      | Статус | Комментарий                                                                          |
| --- | ----------------------------- | ------ | ------------------------------------------------------------------------------------ |
| 1   | Energy + Torque (L1.5)        | ✅      | `SemanticTypeError` в `dbse.semantic`                                                |
| 2   | v > c, Model Breakdown (L5)   | ⚠️     | P3 в тестах с готовым AST; не из фразы «сила 3·10⁸ Н»                                |
| 3   | Неоднозначное «яблоко» (L2)   | ✅      | `AMBIGUITY_HALT` + `/clarify`                                                        |
| 4   | Buckingham π                  | ❌      | SVD / π-группы не реализованы                                                        |
| 5   | exp(5 кг), sin(10 м)          | ✅      | `check_transcendental` в `dbse.dimensional`                                          |
| 6   | Кэш изоморфных задач (L3)     | ⚠️     | LRU+HMAC+`core_version`; не «Q=CV = S=vt» из коробки                                 |
| 7   | Re → турбулентность (L4)      | ⚠️     | Плагин `fluid_mechanics` считает Re и выбирает модель; без текста «сменили Пуазейль» |
| 8   | T < 0 K (термодинамика)       | ❌      | Инвариант `TEMPERATURE_POSITIVE` нет                                                 |
| 9   | Мнение / «кто виноват» (L0.5) | ⚠️     | OPINION → `UNHANDLED` на **англ.** маркерах (`worst`); рус. «худшая» пока → L2       |
| 10  | Спутник 500 кг, 400 км        | ⚠️     | Частично: рецепт **F = m·g**, не G·M/(R+h)² и не P1+Z3 как в спеке                   |


Ниже — **рабочие** примеры (✅ и проверенные ⚠️). Формулировки ответа в MVP проще, чем в маркетинговой спеке (нет `P6`, полей `elapsed_ms` и т.д.): у нас `ProofLevel` **P0–P4**, halt — `halt_reason`.

### ✅ 1. L1.5: нельзя сложить Энергию и Момент силы

Одинаковая размерность ≠ можно складывать. Проверка в библиотеке (тесты: `tests/semantic/test_adversarial.py`):

```python
from dbse.semantic import Operator, SemanticTypeError, affine, check_compatible

try:
    check_compatible(affine("Energy"), affine("Torque"), Operator.ADD)
except SemanticTypeError as exc:
    print(exc)  # Semantic mismatch at L1.5 …
```

Типичное сообщение: `Semantic mismatch at L1.5` … `Energy` vs `Torque`.

Свободный текст «50 Дж + 50 Н·м» **сам** в пайплайн эту ошибку пока не превращает — нужны узлы AST с тегами (этап интеграции L1.5 в compile для таких запросов).

### ⚠️ 2. Инвариант v < c (релятивистский пробой)

В **интеграционном тесте** при ОДУ `dv/dt = 2c` и инварианте `v < c` NUCLEUS останавливает с **P3** `MODEL_BREAKDOWN` (`tests/nucleus/test_adversarial_ode.py`).

Запрос вида «сила 3·10⁸ Н на 1 кг, скорость через 2 с» end-to-end **не** разбирается в полноценную ОДУ с монитором — для демо используйте тест или соберите `PipelineContext` с `ast` + `invariants` как в тесте.

### ✅ 3. L2: неоднозначность «яблоко»

```python
from dbse.pipeline import Pipeline

ctx = Pipeline().run("Сколько стоит яблоко?")
# ctx.halted == True, ctx.halt_reason == AMBIGUITY_HALT
# ctx.model_lattice["candidates"] — варианты интерпретаций
```

Аналогично срабатывает на «Рассчитай, как быстро падает яблоко» (высокая `ambiguity_temperature`).
API: `POST /api/v5/clarify` с тем же запросом.

Точные проценты (65% / 30%) в MVP **не гарантированы** — есть кандидаты и порог halt ≥ 0.6.

### ✅ 5. Трансцендентные функции: аргумент безразмерный

```python
from dbse.dimensional import check_transcendental, DimensionError
from dbse.contracts.dimensions import Dimension

check_transcendental("exp", Dimension.of(1))  # → DimensionError
```

Парсер текста «e^(5 кг)» в полный AST с `exp` в MVP не доведён — правило живёт в L1 и тестах `tests/dimensional/`.

### ⚠️ 6. Semantic cache (L3)

Кэш по `canonical_hash` AST: повторный тот же хеш → быстрый hit (`tests/ribosome/test_cache.py`).
Две разные физические задачи (конденсатор и s = v·t) **не обязаны** дать один хеш — только если совпала структура после нормализации.

### ⚠️ 7. fluid_mechanics: число Рейнольдса

```python
Pipeline().run(
    "...",
    config={"domain_hint": "fluid_mechanics", "viscosity_pa_s": 0.001},
)
```

Плагин считает Re и выбирает `laminar` / `turbulent` / `compressible` модель. Сообщения «вы просили Пуазейль, но Re=500000» в UI **нет** — только выбор модели в trace.

### ⚠️ 9. STS: субъективный вопрос

Работает на маркерах вроде **worst / best** (англ.):

```python
ctx = Pipeline().run("Why is string theory the worst idea in physics?")
# sts_type == "OPINION", halt_reason == UNHANDLED
```

Русское «худшая идея» / «кто виноват» пока часто уходит в **AMBIGUOUS**, не в OPINION — см. `dbse/sts/classifier.py`.

### ✅ 10 (эталон MVP): яблоко 100 г — полный пайплайн

Главный **сквозной** пример (ТЗ + `tests/test_e2e_dod.py`):

```python
ctx = Pipeline().run(
    "С какой силой Земля притягивает яблоко массой 100г?",
    config={"domain_hint": "classical_mechanics"},
)
# solution["value"] ≈ 0.98 N, solution["unit"] == "N"
# proof.level == P2, narrative + expression заполнены
```

Спутник «500 кг на 400 км» сейчас даёт оценку через **F = m·g** (~4.9 kN), а не ньютоновскую гравитацию с G и высотой — для эталона используйте яблоко.

### ❌ 4, 8 — не в MVP

**Buckingham π** и **инвариант положительной температуры** — целевые возможности из спеки; реализации в `dbse/` нет.

### Резюме по «10 сценариям»


| Система умеет в MVP                       | Пока нет                                 |
| ----------------------------------------- | ---------------------------------------- |
| Сказать **нет** (L1.5, Core, частично L5) | Buckingham, T>0 инвариант                |
| Сказать **уточни** (L2)                   | Точные % в lattice как в брошюре         |
| Считать яблоко end-to-end                 | Спутник с G,r,h и P1 narrative           |
| Кэш и защита кэша                         | «Умный» cache hit между разными задачами |


---

## Архитектура (пайплайн)

```
L0  MEMBRANE        (парсинг → строгая схема)
L0.5 STS TYPING     (тип запроса: PHYSICS_COMPUTE / …)
L1  DIMENSIONS      (pass-through; проверки в compile)
L1.5 AFFINE TYPES   (pass-through; теги в compile)
L2  MODEL LATTICE   (неоднозначность → halt / кандидаты)
L3  RIBOSOME        (AST + hash + кэш)
L4  CYTOPLASM       (доменные плагины по domain_hint)
L5  NUCLEUS         (SymPy / ОДУ / Z3 / инварианты)
L6  NARRATIVE       (детерминированный skeleton)
L7  EXPRESSION      (eli5 / academic / business, fallback без LLM)
```

---

## Документация

- `[DBSE v5.0 «Chromosome».txt](DBSE%20v5.0%20%C2%ABChromosome%C2%BB.txt)` — спецификация.
- `[ROADMAP.md](ROADMAP.md)` — план этапов (для разработчиков, не замена README).
- `[docs/TESTING_AND_MENTOR.md](docs/TESTING_AND_MENTOR.md)` — тестирование и Mentor.
- `[docs/spec-notes.md](docs/spec-notes.md)` — принятые решения по слоям.
- `[docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md)` — что в MVP, что отложено.

---

## Статус этапов (кратко)

Этапы **0–12** и **M** — реализованы в коде на `main`. Список с галочками и
закрытыми уязвимостями см. в истории коммитов и `docs/IMPLEMENTATION_STATUS.md`;
полный перечень в предыдущих версиях README сохранён в git-истории при необходимости.

Отложено (не блокирует установку): OpenTelemetry, `schemathesis`, LLM для L7,
подкоманды Mentor `triage`/`promote`/`report`, этап 13+ (новые плагины, IDE).

---

## Частые проблемы


| Симптом                            | Причина                                     | Что сделать                                        |
| ---------------------------------- | ------------------------------------------- | -------------------------------------------------- |
| `no pyproject.toml` в другой папке | `pip install` не в корне Chromosome         | `cd` в папку с `pyproject.toml`                    |
| `solution` = `None`                | Нет `domain_hint` или не распознана масса   | `classical_mechanics`, запрос с `100г` или `100 g` |
| `AMBIGUITY_HALT`                   | «Сколько стоит яблоко?» — цена vs физика    | `/api/v5/clarify` или уточнить запрос              |
| `dbse-api` не найден               | venv не активирован или пакет не установлен | `Activate.ps1` + `pip install -e ".[dev]"`         |



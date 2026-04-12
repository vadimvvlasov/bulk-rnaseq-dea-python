# Bulk RNA-seq Differential Expression Analysis with PyDESeq2

Пайплайн для поиска дифференциально экспрессированных генов (DEGs) из bulk RNA-seq данных с использованием [PyDESeq2](https://pydeseq2.readthedocs.io/) — Python-реализации DESeq2.

## Быстрый старт

```bash
# 1. Установка зависимостей
uv sync

# 2. Загрузка данных (synthetic example)
uv run python scripts/fetch_data.py

# 3. Запуск ноутбука
uv run jupyter notebook rnaseq_deseq2.ipynb
```

## Структура проекта

```
├── pyproject.toml            # Зависимости (uv)
├── rnaseq_deseq2.ipynb       # Основной ноутбук с анализом
├── scripts/
│   └── fetch_data.py         # Загрузка/подготовка данных
├── docs/
│   └── biological_context.md # Геном vs транскриптом, связь с селекцией
├── data/                     # Входные данные (генерируется)
│   ├── counts.csv            # Матрица подсчётов
│   └── metadata.csv          # Метаданные образцов
├── figures/                  # Визуализации (генерируются)
│   ├── ma_plot.png
│   ├── volcano_plot.png
│   ├── pca_plot.png
│   └── pvalue_distribution.png
└── results/                  # Результаты (генерируются)
    ├── deseq2_results.csv    # Полная таблица DEGs
    └── significant_degs.csv  # Только значимые гены
```

## Методология

### DESeq2 Pipeline

1. **Фильтрация** — удаление генов с суммарными counts < 10
2. **Нормализация** — оценка size factors (медиана отношений)
3. **Оценка дисперсий** — fitting Negative Binomial dispersion trend
4. **Моделирование** — NB GLM, оценка Log2 Fold Change
5. **Wald test** — статистическое тестирование для каждого гена
6. **Коррекция BH** — контроль False Discovery Rate (padj)
7. **LFC Shrinkage (apeGLM)** — сжатие зашумлённых оценок LFC

### Биологический контекст

> **Геном** — это «чертёж» организма (что заложено природой). **Транскриптом (РНК)** — это «отчёт о работе» прямо сейчас (какие гены реально активны).

RNA-seq анализ дополняет геномную селекцию: если GBLUP/ssGBLUP предсказывает **потенциал** по SNP-маркерам, то PyDESeq2 показывает **реальную активность** генов в ответ на условия среды, болезнь или стресс.

Подробности: [docs/biological_context.md](docs/biological_context.md)

### Формат входных данных

**Counts matrix** (`counts.csv`):
- Строки: образцы (samples)
- Столбцы: гены (gene symbols/IDs)
- Значения: сырые подсчёты прочтений (raw read counts)

**Metadata** (`metadata.csv`):
- Строки: образцы (совпадают с counts)
- Столбцы: ковариаты (условие, пол, batch и т.д.)
- Ключевой столбец: `condition` (фактор сравнения)

## Источники данных

### Synthetic data (по умолчанию)
```bash
uv run python scripts/fetch_data.py --source synthetic
```

### Собственные данные (CSV)
```bash
uv run python scripts/fetch_data.py \
  --source csv \
  --counts-file my_counts.csv \
  --metadata-file my_metadata.csv
```

### recount3 (реальные RNA-seq данные)
recount3 — это >700k образцов bulk RNA-seq человека и мыши. Данные доступны через AWS Open Data, но требуют R/Bioconductor для парсинга RDS формата.

```bash
# Попытка загрузки (fallback на synthetic, т.к. RDS требует R)
uv run python scripts/fetch_data.py --source recount3 --species human --project SRP009615
```

Для работы с recount3 в Python:
1. Скачайте данные через R: `recount3::create_rse(project='SRP009615')`
2. Экспортируйте в CSV: `write.csv(assay(rse), 'counts.csv')`
3. Загрузите через `--source csv`

## Визуализации

| Plot | Описание |
|------|----------|
| **MA-plot** | Средняя экспрессия vs Log2FC — оценка зависимости эффекта от уровня экспрессии |
| **Volcano plot** | -log10(padj) vs Log2FC — идентификация биологически значимых DEGs |
| **PCA plot** | Кластеризация образцов — проверка разделения по условиям |
| **P-value distribution** | Диагностика качества модели — пик у 0 = хороший сигнал |

## Зависимости

| Пакет | Назначение |
|-------|-----------|
| `pydeseq2` | Основной DEA pipeline (DESeq2 на Python) |
| `pandas` | Обработка табличных данных |
| `numpy` | Численные операции |
| `matplotlib` + `seaborn` | Визуализация |
| `scanpy` | Подготовка для дальнейшего single-cell анализа |
| `jupyter` | Интерактивный анализ |

## Требования

- Python >= 3.11
- `uv` (менеджер пакетов)

## Лицензия

MIT

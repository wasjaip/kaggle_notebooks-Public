# Kaggle notebooks

Коллекция моих публичных решений, соревнований и экспериментов с Kaggle.

**Kaggle:** [kaggle.com/wasjaip](https://www.kaggle.com/wasjaip)  
**Статус профиля:** Competitions Expert

## Портфолио Kaggle

После запуска автоматической синхронизации полный каталог формируется в [`KAGGLE_INDEX.md`](KAGGLE_INDEX.md).

Каждый публичный Kaggle notebook сохраняется в отдельную папку:

```text
kaggle/
└── notebook-slug/
    ├── notebook.ipynb
    ├── kernel-metadata.json
    └── README.md
```

README для каждого решения содержит:

- ссылку на оригинал в Kaggle;
- название решения;
- язык и тип notebook;
- связанное соревнование;
- использованные Kaggle datasets;
- зависимости от других Kaggle notebooks;
- основные разделы notebook.

Тяжёлые результаты выполнения ячеек в GitHub не дублируются — актуальные outputs остаются на Kaggle.

## Основные направления

### Time series и табличные данные

- [Enefit — ensemble LightGBM/CatBoost](enefit-pebop-v1-lgbm-cat-ensemble.ipynb)
- [Optiver — CatBoost](optiver-catboost-v1.ipynb)
- [Optiver — LightGBM + CatBoost](lgbm-catboost-v1.ipynb)
- [Used Cars Price Prediction](auto-yandex-mast-v1.ipynb)

### NLP

- [NLP Watson TPU](nlp-watson-v1-tpu.ipynb)

### Computer Vision

- [EfficientNet experiment](cnn-efficientnet-v1-test.ipynb)

### GPU / performance experiments

- [P100 vs T4 x2](p100-vs-t4-x2.ipynb)
- [SVM RAPIDS](s-v-m-rapids.ipynb)

## Автоматическая синхронизация Kaggle → GitHub

В репозитории есть:

- [`scripts/sync_kaggle.py`](scripts/sync_kaggle.py) — получает список публичных notebooks через официальный Kaggle CLI и обновляет каталог;
- [`.github/workflows/sync-kaggle.yml`](.github/workflows/sync-kaggle.yml) — запускает синхронизацию вручную или автоматически раз в неделю.

### Что нужно настроить один раз

В GitHub открыть:

`Settings → Secrets and variables → Actions → New repository secret`

Создать secret:

```text
KAGGLE_API_TOKEN
```

Токен создаётся в настройках Kaggle в разделе API.

После этого открыть:

`Actions → Sync Kaggle notebooks → Run workflow`

После первого запуска появятся каталог `kaggle/` и файл `KAGGLE_INDEX.md`.

## Назначение репозитория

Этот репозиторий служит единым техническим архивом Kaggle-работ. Самые сильные и законченные решения дополнительно оформляются как отдельные портфолио-проекты с расширенным описанием задачи, архитектуры, подхода, метрик и результатов.

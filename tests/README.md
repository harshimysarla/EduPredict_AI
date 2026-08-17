# EduPredict AI

## Run backend tests

```bash
cd backend
python -m pytest ../tests -x -q
```

## Run ML pipeline tests in isolation

```bash
python -m pytest tests/test_ml_pipeline.py -x -q
```
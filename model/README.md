# model/

Place your trained YOLO model here:

| File | Required | Description |
|------|----------|-------------|
| `albionfisher.pt` | yes | Trained ultralytics YOLO weights (v8+) |
| `classes.yaml` | yes (tracked) | Object class list — source of truth for training and runtime |

Train on your own dataset using the class IDs and names from `classes.yaml`.
Do not reorder or rename classes without updating `classes.yaml`, `docs/SPEC.md`
and noting the change in `progress.md` — the app validates model classes at startup.

Weights (`*.pt`) are gitignored — the model is distributed manually.

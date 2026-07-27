# Recognition Evaluation Toolkit

This experiment measures face-recognition quality from saved images. It does not
use the webcam, database, or live app routes.

## Goal

Use real ML evaluation habits:

- labeled test data
- embedding similarity scores
- threshold sweeps
- precision, recall, F1, and accuracy
- anonymous false-positive checks
- confusion matrix visualization

## Dataset Layout

Known reference photos default to:

```text
backend/known_faces/
```

Add evaluation-only test photos here:

```text
experiments/recognition_eval/dataset/test/
  Mohammad/
    test-1.jpg
    test-2.jpg
  Omar/
    test-1.jpg
  Anonymous/
    unknown-1.jpg
```

Folder name is the true label. Use `Anonymous` for people who should not match
any known person.

Personal photos are gitignored. Do not commit dataset images or generated
reports.

## Run

From the project root:

```bash
cd backend
source venv/bin/activate
pip install -r requirements-dev.txt
cd ..
backend/venv/bin/python experiments/recognition_eval/evaluate_faces.py
```

Optional threshold sweep:

```bash
backend/venv/bin/python experiments/recognition_eval/evaluate_faces.py \
  --thresholds 0.35:0.75:0.02 \
  --current-threshold 0.45
```

## Outputs

Generated files are saved under:

```text
experiments/recognition_eval/results/
```

Expected reports:

```text
predictions.csv
score_distribution.csv
per_label_metrics.csv
threshold_report.csv
confusion_matrix.png
threshold_plot.png
recommended_threshold.txt
summary.json
```

Report meanings:

- `predictions.csv`: one row per test image at the current threshold.
- `score_distribution.csv`: best-match score per image before applying a threshold.
- `per_label_metrics.csv`: precision, recall, F1, and support per label.
- `threshold_report.csv`: accuracy and error rates across all swept thresholds.
- `confusion_matrix.png`: true label vs predicted label at the current threshold.
- `threshold_plot.png`: threshold tradeoff chart for accuracy, F1, and error rates.
- `summary.json`: machine-readable experiment summary and dataset warnings.

## How To Explain It

Example:

```text
At threshold 0.45, Mohammad is recognized correctly but Anonymous has false positives.
After sweeping thresholds, 0.52 gives better macro F1 and fewer false known matches.
```

This is the bridge from a working computer-vision demo to a real ML engineering
project: we are measuring model behavior before changing production thresholds.

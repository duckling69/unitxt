from src.unitxt import add_to_catalog
from src.unitxt.metrics import SubstringAccuracy
from src.unitxt.test_utils.metrics import test_metric

metric = SubstringAccuracy()

predictions = ["A", "B", "C"]
references = [["B", "AB", " "], ["A", "b"], ["c"]]

instance_targets = [
    {"substring_accuracy": 1.0, "score": 1.0, "score_name": "substring_accuracy"},
    {"substring_accuracy": 0.0, "score": 0.0, "score_name": "substring_accuracy"},
    {"substring_accuracy": 0.0, "score": 0.0, "score_name": "substring_accuracy"},
]

global_target = {"substring_accuracy": 0.33, "score": 0.33, "score_name": "substring_accuracy"}

outputs = test_metric(
    metric=metric,
    predictions=predictions,
    references=references,
    instance_targets=instance_targets,
    global_target=global_target,
)

add_to_catalog(metric, "metrics.substring_accuracy", overwrite=True)
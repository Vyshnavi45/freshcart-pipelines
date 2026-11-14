
if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

import pandas as pd
from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)


@transformer
def evaluate_model(data, *args, **kwargs):
    actual = data['y_test']
    predicted = data['predictions']

    labels = [0, 1, 2]

    cm = confusion_matrix(actual, predicted, labels=labels)

    confusion_table = pd.DataFrame(
        cm,
        index=['Actual 0', 'Actual 1', 'Actual 2'],
        columns=['Predicted 0', 'Predicted 1', 'Predicted 2']
    )

    metrics_table = pd.DataFrame({
        'Metric': ['Accuracy', 'Precision', 'Recall', 'F1 Score'],
        'Score': [
            accuracy_score(actual, predicted),
            precision_score(actual, predicted, average='macro', zero_division=0),
            recall_score(actual, predicted, average='macro', zero_division=0),
            f1_score(actual, predicted, average='macro', zero_division=0)
        ]
    })

    return {
        'confusion_matrix': confusion_table,
        'metrics': metrics_table
    }


@test
def test_output(output, *args):
    assert output is not None
    assert output['confusion_matrix'].shape == (3, 3)
    assert len(output['metrics']) == 4

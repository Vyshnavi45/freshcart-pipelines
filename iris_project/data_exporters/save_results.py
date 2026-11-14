if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

import pandas as pd


@data_exporter
def save_results(data, *args, **kwargs):
    results = pd.DataFrame({
        'actual': data['y_test'],
        'predicted': data['predictions']
    })

    results.to_csv('iris_predictions.csv', index=False)

    return results


@test
def test_output(output, *args):
    assert output is not None
    assert len(output) == 30
    assert 'actual' in output.columns
    assert 'predicted' in output.columns
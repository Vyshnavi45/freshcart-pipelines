if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

from sklearn.datasets import load_iris


@transformer
def validate_iris(data, *args, **kwargs):
    iris = load_iris(as_frame=True)
    df = iris.frame

    missing_values = int(df.isnull().sum().sum())
    number_of_classes = int(df['target'].nunique())

    assert missing_values == 0, "Missing values found"
    assert number_of_classes == 3, "Expected exactly 3 classes"

    return {
        'rows': int(len(df)),
        'missing_values': missing_values,
        'number_of_classes': number_of_classes
    }


@test
def test_output(output, *args):
    assert output is not None
    assert output['rows'] == 150
    assert output['missing_values'] == 0
    assert output['number_of_classes'] == 3
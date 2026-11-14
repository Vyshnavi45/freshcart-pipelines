if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

from sklearn.datasets import load_iris as sklearn_load_iris


@data_loader
def load_iris(*args, **kwargs):
    iris = sklearn_load_iris(as_frame=True)
    return iris.frame


@test
def test_output(output, *args):
    assert output is not None
    assert len(output) == 150
    assert output.shape[1] == 5
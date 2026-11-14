if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score


@transformer
def train_model(data, *args, **kwargs):
    model = DecisionTreeClassifier(
        max_depth=kwargs.get('max_depth', 5),
        random_state=42
    )

    X_train = data['X_train']
    X_test = data['X_test']

    y_train = [
        int(item['target']) if isinstance(item, dict) else int(item)
        for item in data['y_train']
    ]

    y_test = [
        int(item['target']) if isinstance(item, dict) else int(item)
        for item in data['y_test']
    ]

    model.fit(X_train, y_train)

    predictions = model.predict(X_test).tolist()

    accuracy = float(accuracy_score(y_test, predictions))

    return {
        'predictions': predictions,
        'y_test': y_test,
        'test_accuracy': accuracy
    }


@test
def test_output(output, *args):
    assert output is not None
    assert output['test_accuracy'] >= 0.70
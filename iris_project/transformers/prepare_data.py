try:
    from mage_ai.data_preparation.decorators import transformer, test
except ImportError:
    def transformer(func):
        return func

    def test(func):
        return func

from sklearn.model_selection import train_test_split


def transform(data):
    result = data.copy()

    train_indices, test_indices = train_test_split(
        result.index,
        test_size=0.2,
        random_state=42,
        stratify=result['target']
    )

    result['split'] = 'train'
    result.loc[test_indices, 'split'] = 'test'

    return result


@transformer
def prepare_data(data, *args, **kwargs):
    result = transform(data)

    train = result[result['split'] == 'train']
    test_data = result[result['split'] == 'test']

    X_train = train.drop(columns=['target', 'split'])
    y_train = train['target']

    X_test = test_data.drop(columns=['target', 'split'])
    y_test = test_data['target']

    return {
        'X_train': X_train,
        'X_test': X_test,
        'y_train': y_train,
        'y_test': y_test
    }


@test
def test_output(output, *args):
    assert output is not None
    assert len(output['X_train']) == 120
    assert len(output['X_test']) == 30
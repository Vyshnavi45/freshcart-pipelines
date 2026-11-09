try:
    from mage_ai.data_preparation.decorators import transformer
except ImportError:
    def transformer(function):
        return function


from sklearn.model_selection import train_test_split


@transformer
def transform(df, *args, **kwargs):
    train_indices, test_indices = train_test_split(
        df.index,
        test_size=0.3,
        random_state=42
    )

    result = df.copy()
    result["split"] = "train"
    result.loc[test_indices, "split"] = "test"

    return result
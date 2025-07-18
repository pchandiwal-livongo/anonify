from faker import Faker
from collections import OrderedDict

fake = Faker()

def randomize_column(series, params):
    """
    Randomizes the values in a pandas Series column based on the specified method and parameters.

    Args:
        series (pandas.Series): The pandas Series column to be randomized.
        params (dict): A dictionary containing the method and parameters for randomization.

    Returns:
        pandas.Series: The randomized pandas Series column.

    Raises:
        KeyError: If the 'method' key is not present in the params dictionary.
    """
    method = params['method']
    elements = params['elements']
    
    if method == 'random_element':
        return series.apply(lambda x: fake.random_element(elements))
    elif method == 'random_elements':
        length = params.get('length', 1)
        unique = params.get('unique', False)
        weights = params.get('weights', None)
        if weights:
            elements_dict = OrderedDict(zip(elements, weights))
            result = series.apply(lambda x: fake.random_elements(elements_dict, length=length, unique=unique))
        else:
            result = series.apply(lambda x: fake.random_elements(elements, length=length, unique=unique))
        
        # If length is 1, extract the single element from the list
        if length == 1:
            result = result.apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x)
        
        return result
    elif method == 'random_int':
        min_value = params.get('min', 0)
        max_value = params.get('max', 9999)
        step = params.get('step', 1)
        return series.apply(lambda x: fake.random_int(min=min_value, max=max_value, step=step))

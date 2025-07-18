from .modules import fake_column, hash_column, null_column, randomize_column, obfuscate_column

def preprocess(dataframe, config):
    # Validate configuration structure
    if 'columns' not in config:
        raise ValueError("Configuration must contain 'columns' key")
    
    # Valid anonymization methods
    valid_methods = {'hash', 'fake', 'null_column', 'randomize', 'obfuscate', 'do_not_change'}
    
    for column, actions in config['columns'].items():
        # Check if column exists in DataFrame
        if column not in dataframe.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame. Available columns: {list(dataframe.columns)}")
        
        for action, params in actions.items():
            # Validate method is supported
            if action not in valid_methods:
                raise ValueError(f"Unknown anonymization method '{action}' for column '{column}'. Valid methods: {valid_methods}")
            
            if action == 'hash':
                salt = params.get('salt', '')
                dataframe[column] = hash_column(dataframe[column], salt)
            elif action == 'fake':
                dataframe[column] = fake_column(dataframe[column], params)
            elif action == 'null_column':
                dataframe = null_column(dataframe, column)
            elif action == 'randomize':
                dataframe[column] = randomize_column(dataframe[column], params)
            elif action == 'obfuscate':
                dataframe[column] = obfuscate_column(dataframe[column], params)
            elif action == 'do_not_change':
                continue
    return dataframe

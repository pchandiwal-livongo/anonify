from .modules import fake_column, hash_column, null_column, randomize_column, obfuscate_column

def preprocess(dataframe, config):
    for column, actions in config['columns'].items():
        for action, params in actions.items():
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

from faker import Faker

fake = Faker()

def fake_column(series, fake_type):
    # Handle both old format (string) and new format (dict with fake_type key)
    if isinstance(fake_type, dict):
        actual_fake_type = fake_type.get('fake_type', fake_type.get('type', 'name'))
    else:
        actual_fake_type = fake_type
    
    # Ensure we have a string
    if not isinstance(actual_fake_type, str):
        actual_fake_type = str(actual_fake_type)
    
    fake_func = getattr(fake, actual_fake_type)
    return series.apply(lambda x: fake_func())

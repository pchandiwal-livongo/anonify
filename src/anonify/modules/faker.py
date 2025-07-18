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
    
    # Security check: only allow safe faker methods (no private/protected attributes)
    if actual_fake_type.startswith('_') or '.' in actual_fake_type:
        raise ValueError(f"Invalid fake_type '{actual_fake_type}'. Only public faker methods are allowed.")
    
    # Validate that the method exists
    if not hasattr(fake, actual_fake_type):
        raise ValueError(f"Unknown faker method '{actual_fake_type}'. Available methods include: name, email, address, etc.")
    
    fake_func = getattr(fake, actual_fake_type)
    return series.apply(lambda x: fake_func())

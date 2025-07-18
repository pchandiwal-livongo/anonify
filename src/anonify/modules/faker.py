from faker import Faker

fake = Faker()

def fake_column(series, fake_type):
    fake_func = getattr(fake, fake_type)
    return series.apply(lambda x: fake_func())

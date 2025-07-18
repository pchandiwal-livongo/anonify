import pandas as pd
from faker import Faker
import random

fake = Faker()

def obfuscate_column(series, params):
    format = params.get('format', '%Y-%m-%d')
    threshold = params.get('threshold', 30)
    min_range = pd.to_datetime(params.get('min_range', '1900-01-01'))
    max_range = pd.to_datetime(params.get('max_range', '2100-01-01'))
    
    def obfuscate_date(date):
        if pd.isnull(date):
            return date
        if not isinstance(date, pd.Timestamp):
            date = pd.to_datetime(date)
        delta = pd.Timedelta(days=random.randint(-threshold, threshold))
        obfuscated_date = date + delta
        if obfuscated_date < min_range or obfuscated_date > max_range:
            obfuscated_date = date
        return obfuscated_date.strftime(format)
    
    return series.apply(obfuscate_date)

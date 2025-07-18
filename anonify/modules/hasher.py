import hashlib

def hash_column(series, salt):
    return series.apply(lambda x: hashlib.sha256((str(x) + salt).encode()).hexdigest())

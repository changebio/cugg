# AUTOGENERATED! DO NOT EDIT! File to edit: 04_Utils.ipynb (unless otherwise specified).

__all__ = ['shorten_id']

# Cell
from xxhash import xxh32 as xxh

# Cell
def shorten_id(x):
    return x if len(x) < 30 else f"{x.split('_')[0]}_{xxh(x).hexdigest()}"
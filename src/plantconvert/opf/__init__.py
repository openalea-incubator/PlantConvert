import xml.etree.ElementTree as ET
from . import reader,writer
from math import isnan

def float_to_string(f):
    if isnan(f):
        return 'NaN'
    else:
        return str(f)


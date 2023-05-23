from math import isnan

def float_to_string(f):
    """Converts a float to a string

    Args:
        f (float): float number

    Returns:
        string: string convertion of the float
    """
    if isnan(f):
        return 'NaN'
    else:
        return str(f)

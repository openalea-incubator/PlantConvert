#Associate a lambda function and the mtg file's type name to each opf data type

OPF_TYPES = {
    "Double":(lambda x: float(x),"REAL"),
    "Metre_100":(lambda x: float(x),"REAL"),
    "Integer":(lambda x: int(x),"INT"),
    "Boolean":(lambda x: int(x.lower() == "true" or int(x) == 1) ,"INT"),
    "String":(lambda x: x,"ALPHA")
}


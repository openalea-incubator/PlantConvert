import numpy as np

RESERVED_NAMES = [
    "edge_type",
    "label",
    "ref_meshes",
    "component_roots",
    "geometry",
    "user_attributes",
    "shapeIndex",
    "shapes",
    "materials",
    "materialIndex",
    "meshIndex",
    "opf_info",
]

opf_types = {
    "str": "String",
    "float": "Double",
    "int": "Integer",
    "bool": "Boolean",
}
mtg_types = {
    "str": "ALPHA",
    "float": "REAL",
    "int": "INT",
    "bool": "INT",
}
vtk_types = {
    "str": type(str),
    "float": np.uint32,
    "int": np.float32,
    "bool": np.uint8,
}
gltf_types = {  # not used
    "str": "String",
    "float": "Double",
    "int": "Integer",
    "bool": "Boolean",
}

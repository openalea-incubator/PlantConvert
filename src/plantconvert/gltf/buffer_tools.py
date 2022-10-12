from struct import unpack
from . import gltf
from .. import binary_tools

# consider the gltf as a dictionary
GLTF_DICT = gltf.__dict__

# associate component types with with component length
COMPONENT_NB = {
    gltf.SCALAR : 1,
    gltf.VEC2 : 2,
    gltf.VEC3 : 3,
    gltf.VEC4 : 4,
    gltf.MAT2 : 4,
    gltf.MAT3 : 9,
    gltf.MAT4 : 16
}

def get_key(d : dict, value):
    for k,v in d.items():
        if v == value:
            return k

def get_buffer(acsr : gltf.Accessor, g : gltf.GLTF2):
    "Get the buffer referenced by the accessor in a gltf asset"
    return g.buffers[g.bufferViews[acsr.bufferView].buffer]

def get_data(byte_string, acsr : gltf.Accessor, buffer_view : gltf.BufferView):
    
    dtype = get_key(GLTF_DICT, acsr.componentType)   
    component_nb = COMPONENT_NB[acsr.type]
    offset = acsr.byteOffset + buffer_view.byteOffset
    count = acsr.count
    
    unpacked = binary_tools.unpack_byte_string(byte_string, offset, count, component_nb, dtype)

    if buffer_view.target == gltf.ELEMENT_ARRAY_BUFFER:
        unpacked = [tuple(unpacked[i:i+3]) for i in range(0,len(unpacked),3)]
    return unpacked
import struct

# define a dictionary that associate the type name to its format char and to its byte size
FORMAT_CHAR_AND_SIZE = {
    "byte":("b",1),
    "ubyte":("B",1),
    "short":("h",2),
    "ushort":("H",2),
    "unsigned_short":("H",2),
    "uint32":("I",4),
    "float":("f",4)
}

def type_info(dtype):
    try : 
        return FORMAT_CHAR_AND_SIZE[dtype.lower()]
    except KeyError:
        raise KeyError("This the dtype %s is not supported "%(dtype.lower()))


def pack_vec_array(vec_array, dtype):
    """
    This function transform the input array of vectors into a binary string that you can write into a file when you open it by 'wb'
    It returns a binary string that store the data in compact way.

    This function always pack bytes in litte endian order
    """

    f,size = type_info(dtype)
    
    n = len(vec_array)
    m = len(vec_array[0])

    byte_string = b""
    
    for vec in vec_array:
        byte_string += struct.pack("<"+f*m,*vec)
    return byte_string

def unpack_byte_string(byte_string, offset, count, component_nb, dtype):
    """
    unpack data from the byte string.
    The stride is implicit and is considered to be component_nb * dtype_size
    """
    format, size = type_info(dtype)

    byte_length = size*count*component_nb
    
    if component_nb > 1: 
        return list(struct.iter_unpack("<"+format*component_nb, byte_string[offset:offset+byte_length]))
    else:
        return struct.unpack("<"+format*count, byte_string[offset:offset+byte_length])
        


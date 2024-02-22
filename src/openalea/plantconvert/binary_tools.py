import struct

# This dictionary associates the type name to its format char and to its byte size
FORMAT_CHAR_AND_SIZE = {
    "byte": ("b", 1),
    "ubyte": ("B", 1),
    "short": ("h", 2),
    "ushort": ("H", 2),
    "unsigned_short": ("H", 2),
    "uint32": ("I", 4),
    "float": ("f", 4),
}


def _type_info(dtype):
    try:
        return FORMAT_CHAR_AND_SIZE[dtype.lower()]
    except KeyError:
        raise KeyError("This the dtype %s is not supported " % (dtype.lower()))


def pack_vec_array(vec_array, dtype):
    """Transform the input array of vectors into a binary string.

    :param vec_array: list of vectors
    :type vec_array: array
    :param dtype: data type
    :type dtype: str
    :return: binary string that store the data in compact way, and always pack bytes
    in litte endian order. You can write the binary string into a file when you open it by 'wb'.
    :rtype: bytes
    """
    f, size = _type_info(dtype)

    len(vec_array)
    m = len(vec_array[0])

    byte_string = b""

    for vec in vec_array:
        byte_string += struct.pack("<" + f * m, *vec)
    return byte_string


def _unpack_byte_string(byte_string, offset, count, component_nb, dtype):
    """Unpacks data from the byte string. The stride is implicit and is considered to be component_nb * dtype_size.

    :param byte_string: binary string
    :type byte_string: bytes
    :param offset: offset in the byte string
    :type offset: int
    :param count: number of elements to unpack
    :type count: int
    :param component_nb: number of components in the vector
    :type component_nb: int
    :param dtype: data type
    :type dtype: str
    :return: list of vectors
    :rtype: list
    """
    format, size = _type_info(dtype)

    byte_length = size * count * component_nb

    if component_nb > 1:
        return list(
            struct.iter_unpack(
                "<" + format * component_nb, byte_string[offset : offset + byte_length]
            )
        )
    else:
        return struct.unpack(
            "<" + format * count, byte_string[offset : offset + byte_length]
        )

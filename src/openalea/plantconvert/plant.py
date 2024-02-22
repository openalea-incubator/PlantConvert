from warnings import warn

import openalea.mtg as mtg
from openalea.mtg.algo import orders

from openalea.plantconvert.gltf import reader as readerGltf
from openalea.plantconvert.gltf import writer as writerGltf
from openalea.plantconvert.opf import reader as readerOpf
from openalea.plantconvert.opf import writer as writerOpf
from openalea.plantconvert.vtk import reader as readerVtk
from openalea.plantconvert.vtk import writer as writerVtk

from openalea.plantconvert.util import gltf_types, mtg_types, opf_types, vtk_types, RESERVED_NAMES


class Plant(object):
    """General interface for plantconvert.

    This class allows to read from different file types and to export other file types.

    The supported types are :
        .mtg .opf .vtk .gltf

    :param file: name of the file to read using the read method. Defaults to None.
    :type file: str, optional
    :param ignored_attrs: a list of attributes that will not appear in the final exported
        file in addition to attributes from `RESERVED_NAMES`. Defaults set to empty list.
    :type ignored_attrs: list of string, optional
    :param verbose: verbose mode, more information will be printed on the screen if you activate it.
        Defaults to False.
    :type verbose: bool, optional
    """

    def __init__(self, file: str = "None", ignored_attrs=[], verbose=False):
        """Plant object constructor."""
        self.ignored_attrs = RESERVED_NAMES + ignored_attrs
        self.verbose = verbose
        self.mtg = mtg.MTG()
        self.file = file

    def _warn(self, message):
        if self.verbose:
            warn(message)

    def _get_file_extension(self, filename: str = "") -> str:
        """Get the file extension of the file of the Plant object or of the filename (if provided).

        :param filename: name of the file. Defaults to empty, and returns the file extension of
            the Plant.file attribute.
        :type filename: str, optional
        :return: file extension
        :rtype: string
        """
        if filename == "":
            return self.file.split(".")[-1]
        else:
            return filename.split(".")[-1]

    def read(self):
        """Analyse file type from extension and reads it.

        This method also prepare the self.mtg object so that it can be written again in any other file format.
        """
        file_extension = self._get_file_extension()

        if file_extension == "opf":
            self.mtg = readerOpf.Opf(self.file).read_opf()

        elif file_extension == "mtg":
            self.mtg = mtg.MTG(self.file)

        elif file_extension == "glb" or file_extension == "gltf":
            self.mtg_builder = readerGltf.mtg_builder(self.file)
            self.mtg = self.mtg_builder.build()

        elif file_extension == "vtk" or file_extension == "vtp":
            self.mtg = readerVtk.mtg_from_polydata(self.file)

        else:
            self._warn(
                "File format not detected or not supported yet. \
                Available formats so far are .mtg .opf .vtk .gltf"
            )

    def _get_attribute_types(self, file_extension, properties_names):
        if file_extension == "mtg":
            dict_types = mtg_types
        elif file_extension == "opf":
            dict_types = opf_types
        elif file_extension == "vtk" or file_extension == "vtp":
            dict_types = vtk_types
        elif file_extension == "glb" or file_extension =="gltf":
            dict_types = gltf_types
        types = []
        for names in properties_names:
            try:
                val = next(iter(self.mtg.property(names).values()))
            except StopIteration:
                self._warn("No value is associated to the property name %s" % (names))
                types.append("String")
                continue
            if isinstance(val, str):
                types.append(dict_types["str"])
            elif isinstance(val, float):
                types.append(dict_types["float"])
            elif isinstance(val, int):
                types.append(dict_types["int"])
            elif isinstance(val, bool):
                types.append(dict_types["bool"])
        return types

    def write(self, filename):
        """Write the Plant object to file.

        :param filename: output file.
            Extension will determine which format will be used
        :type filename: string
        """
        properties_names = list(set(self.mtg.property_names()) - set(self.ignored_attrs))
        file_extension = self._get_file_extension(filename)
        types = self._get_attribute_types(file_extension, properties_names)

        if file_extension == "mtg":
            properties = list(zip(properties_names, types))
            max_order = max(list(orders(self.mtg).values()))
            text = mtg.io.write_mtg(self.mtg, properties=properties, nb_tab=max_order + 1)
            with open(filename, "w") as file:
                file.write(text)

        elif file_extension == "opf":
            properties = dict(zip(properties_names, types))
            writerOpf.write_opf(self.mtg, filename, features=properties)

        elif file_extension == "glb" or file_extension =="gltf":
            self.gltf_builder = writerGltf.gltf_builder(self.mtg, properties_names)
            self.gltf_builder.build()
            self.gltf_builder.gltf.save(filename)

        elif file_extension == "vtk" or file_extension == "vtp":
            properties = dict(zip(properties_names, types))
            self.polydata, label_dict = writerVtk.polydata(self.mtg, scalar_features=properties)
            writerVtk.write(filename[:-4], self.polydata, label_dict, binary=True, XML=True)


def plant_from_mtg(g: mtg.MTG) -> Plant:
    """Generate a plant object from an mtg.MTG object.

    Note: This can be usefull if we couple this package to another openalea
    package and want to save to another format.

    :param g: mtg object of the plant we later want to write
    :type g: mtg.MTG
    :return: Plant object that embeds the mtg.MTG objects.
    :rtype: plantconvert.Plant
    """
    p = Plant("")
    p.mtg = g

    return p

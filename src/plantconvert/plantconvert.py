import openalea.mtg as mtg
import numpy as np
from openalea.mtg.algo import orders

from . import gltf, opf, vtk


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

class Plant(object):
    """General interface for plantconvert.
    This class allows to read from different file types and to export 
    other file types.

    The supported types are : 
        .mtg .opf .vtk .gltf

    """
    
    def __init__(self, file : str = None, ignored_name = None, verbose = False):
        """Initialize a Plant object.

        Args:
            file (str, optional): name of the file to read using the read method. Defaults to None.
            ignored_name (list of string, optional): a list of attributes that will not appear in the final exported file. Defaults to None.
            verbose (bool, optional): verbose mode, more information will be printed on the screen if you activate it. Defaults to False.
        """
        if ignored_name is None:
            self.ignored_name = RESERVED_NAMES
        else:
            self.ignored_name = RESERVED_NAMES + ignored_name
        self.verbose = verbose
        self.mtg = mtg.MTG()
        self.file = file

    def _warn(self, message):
        if self.verbose:
            warn(message)

    def read(self):
        """Analyse file type from extension and reads it.
        This method also prepare the self.mtg object so that it can be written again in any other file format.
        """

        if self.file.endswith("opf"):
            self.mtg = opf.reader.Opf(self.file).read_opf()

        elif self.file.endswith("mtg"):
            self.mtg = mtg.MTG(self.file)

        elif self.file.endswith("glb") or self.file.endswith("gltf"):
            self.mtg_builder = gltf.reader.mtg_builder(self.file)
            self.mtg = self.mtg_builder.build()
        
        elif self.file.endswith("vtk") or self.file.endswith("vtp"):
            self.mtg = vtk.reader.mtg_from_polydata(self.file)
            
        else:
            self._warn("File format not detected or not supported yet. Available formats so far are .mtg .opf .vtk .gltf")
            

    def write(self, filename):
        """Write the Plant object.
        
        Args:
            filename (string): output file. Extension will determine which format will be used
        """

        properties_names = list(set(self.mtg.property_names()) - set(self.ignored_name))

        if filename.endswith("mtg"):
            types = _get_attribute_types_mtg(self.mtg, properties_names)
            properties = list(zip(properties_names, types))
            max_order = max(list(orders(self.mtg).values()))
            text = mtg.io.write_mtg(self.mtg,properties=properties,nb_tab = max_order+1)

            with open(filename,'w') as file:
                file.write(text)

        elif filename.endswith("opf"):
            types = self._get_attribute_types(properties_names)
            properties = dict(zip(properties_names, types))
            opf.writer.write_opf(self.mtg, filename, features=properties)

        elif filename.endswith("glb") or filename.endswith("gltf"):
            self.gltf_builder = gltf.writer.gltf_builder(self.mtg, properties_names)
            self.gltf_builder.build()
            self.gltf_builder.gltf.save(filename)

        elif filename.endswith("vtp"):
            types = _get_attribute_types_vtk(self.mtg, properties_names)
            properties = dict(zip(properties_names, types))
            self.polydata, label_dict = vtk.writer.polydata(self.mtg, scalar_features = properties)
            vtk.writer.write(filename[:-4], self.polydata, label_dict, binary=True, XML=True)
            
    def _get_attribute_types(self, properties_names):
        g = self.mtg
        types = []
        for names in properties_names:
            try:
                val = next(iter(g.property(names).values()))
            except StopIteration:
                self._warn("No value is associated to the property name %s"%(names))
                types.append("String")
                continue
            # print(val)
            if isinstance(val, str):
                types.append("String")
            elif isinstance(val, float):
                types.append("Double")
            elif isinstance(val, int):
                types.append("Integer")
            elif isinstance(val, bool):
                types.append("Boolean")
            print(names, types[-1])
        return types

def _get_attribute_types_mtg(g : mtg.MTG, properties_names):
    
    types = []
    for names in properties_names:
        val = next(iter(g.property(names).values()))
        # print(val)
        if isinstance(val, str):
            types.append("ALPHA")
        elif isinstance(val, float):
            types.append("REAL")
        elif isinstance(val, int):
            types.append("INT")
        elif isinstance(val, bool):
            types.append("INT")
        # print(types[-1])
    return types

def _get_attribute_types_vtk(g : mtg.MTG, properties_names):
    types = []
    for names in properties_names:
        val = next(iter(g.property(names).values()))
        if isinstance(val, str):
            types.append(type(str))
        elif isinstance(val, int):
            types.append(np.uint32)
        elif isinstance(val, float):
            types.append(np.float32)
        elif isinstance(val, bool):
            types.append(np.uint8)
    return types

def plant_from_mtg(g: mtg.MTG):
    """Generates a plant object from an mtg.MTG object.
    Note: This can be usefull if we couple this package to another openalea package and want to save to another format.

    Args:
        g (mtg.MTG): mtg object of the plant we later want to write

    Returns:
        plantconvert.Plant: plant object that embeds the mtg.MTG objects. 
    """
    p = Plant('')
    p.mtg = g
    
    return p
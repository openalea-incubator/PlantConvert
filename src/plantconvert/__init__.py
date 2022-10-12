
from warnings import warn
import numpy as np
import numpy.linalg as npl

import openalea.mtg as mtg
from openalea.mtg.algo import orders
import openalea.plantgl.all as pgl

from . import binary_tools, geometry, material, matrix
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

class io(object):
    """
    This object allows to build a mtg from different file types or to export a mtg into different file types.

    The supported types are : 
        .mtg .opf .vtk .gltf
    
    """
    def __init__(self, file : str = None, ignored_name = None, verbose = False):
        """
        Initialize an io object.
        Input param : 
        file (string) : if you want to use the method io.read you should initialize the object with the file name that you want to read.

        ignored_name (list of string): a list of attributes that will not appear in the final exported file

        verbose (bool): verbose mode, more information will be printed on the screen if you activate it
            
        """
        if ignored_name is None:
            self.ignored_name = RESERVED_NAMES
        else:
            self.ignored_name = RESERVED_NAMES + ignored_name
        self.verbose = verbose
        self.g = mtg.MTG()
        self.file = file

    def _warn(self, message):
        if self.verbose:
            warn(message)

    def read(self):
        """
        Analyse file type and read the file.
        This method also prepare the self.g object so that it can be written again in any other file format.
        
        """

        if self.file.endswith("opf"):
            self.opf = opf.reader.Opf(self.file)
            self.g = self.opf.read_opf()

        elif self.file.endswith("mtg"):
            self.g = mtg.MTG(self.file)

        elif self.file.endswith("glb") or self.file.endswith("gltf"):
            self.mtg_builder = gltf.reader.mtg_builder(self.file)
            self.g = self.mtg_builder.build()
        
        elif self.file.endswith("vtk") or self.file.endswith("vtp"):
            self.g = vtk.reader.mtg_from_polydata(self.file)
            
            

    def write(self, filename):
        """ Output the mtg file in the path
            Inputs : 
            Path : the path where we write the output file
            filename : the filename of the mtg without .mtg extension
        """

        properties_names = list(set(self.g.property_names()) - set(self.ignored_name))

        if filename.endswith("mtg"):
            types = _get_attribute_types_mtg(self.g, properties_names)
            properties = list(zip(properties_names, types))
            max_order = max(list(orders(self.g).values()))
            text = mtg.io.write_mtg(self.g,properties=properties,nb_tab = max_order+1)

            with open(filename,'w') as file:
                file.write(text)
            return text

        elif filename.endswith("opf"):
            types = self._get_attribute_types(properties_names)
            properties = dict(zip(properties_names, types))
            opf.writer.write_opf(self.g, filename, features=properties)

        elif filename.endswith("glb") or filename.endswith("gltf"):
            self.gltf_builder = gltf.writer.gltf_builder(self.g, properties_names)
            self.gltf_builder.build()
            self.gltf_builder.gltf.save(filename)

        elif filename.endswith("vtp"):
            types = _get_attribute_types_vtk(self.g, properties_names)
            properties = dict(zip(properties_names, types))
            self.polydata, label_dict = vtk.writer.polydata(self.g, scalar_features = properties)
            vtk.writer.write(filename[:-4], self.polydata, label_dict, binary=True, XML=True)
            
    def _get_attribute_types(self, properties_names):
        g = self.g
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
        



        
        
    

# from math import isnan
# import pygltflib as gltf
# import openalea.mtg.mtg as mtg
# import openalea.plantgl.all as pgl
# from . import utils
# from .maths import get_matrix4

from math import isnan

from . import gltf
from . import buffer_tools
from .. import mtg
from .. import pgl
from .. import np
from ..geometry import taper_along_x, transformed_from_mat

class mtg_builder(object):

    def __init__(self, filename):
        self.gltf = gltf.GLTF2.load(filename)
        self.g = mtg.MTG()

    def build(self):
        self._read_meshes()
        self._read_topology()
        self.g.add_property("geometry")
        for s in self.g.scales_iter():
            self._read_geometry(s)
        return self.g 

    def _read_meshes(self):
        self.data = []
        self.g.add_property("ref_meshes")
        root = self.g.root
        self.g.node(root).ref_meshes = []
        for mesh in self.gltf.meshes:
            if len(mesh.primitives) > 1 or len(mesh.weights) > 0:
                raise NotImplementedError("Multiple primitives meshes are not supported yet")
            
            primitive = mesh.primitives[0]

            pos_ind = primitive.attributes.POSITION
            normal_ind = primitive.attributes.NORMAL
            tex_ind = primitive.attributes.TEXCOORD_0
            indices_ind = primitive.indices

            # pos, normal, tex, indices are supposed to use the same buffer
            buffer = buffer_tools.get_buffer(self.gltf.accessors[pos_ind], self.gltf)
            data = self.gltf.get_data_from_buffer_uri(buffer.uri)
            #self.data.append(data)
            
            # read positions:
            accessor = self.gltf.accessors[pos_ind]
            buffer_view = self.gltf.bufferViews[accessor.bufferView]
            pos = buffer_tools.get_data(data, accessor, buffer_view)
            
            #read normals:
            accessor = self.gltf.accessors[normal_ind]
            buffer_view = self.gltf.bufferViews[accessor.bufferView]
            normal = buffer_tools.get_data(data, accessor, buffer_view)

            #read texture:
            try:
                accessor = self.gltf.accessors[tex_ind]
            except TypeError:
                tex = []
            else:
                buffer_view = self.gltf.bufferViews[accessor.bufferView]
                tex = buffer_tools.get_data(data, accessor, buffer_view)

            #read indices:
            accessor = self.gltf.accessors[indices_ind]
            buffer_view = self.gltf.bufferViews[accessor.bufferView]
            indices = buffer_tools.get_data(data, accessor, buffer_view)
            triangles = pgl.TriangleSet()
            triangles.pointList = pos
            triangles.normalList = normal
            if len(tex) > 0:
                triangles.texCoordList = tex
            triangles.indexList = indices
            self.g.node(root).ref_meshes.append(triangles)
        self.taper_x = taper_along_x(self.g.node(root).ref_meshes)

    def _read_attributes(self, vid):
        node = self.gltf.nodes[vid]
        extras = node.extras

        for k,value in extras.items():
            if k not in ["scale", "edge_type","top","base","component_roots"]:
                setattr(self.g.node(vid), k, value)
            
        

    def _read_topology(self):
        self.max_scale = len(self.gltf.scenes) - 1
        
        for scale, scene in enumerate(self.gltf.scenes):
            # each scene contains the root node of a scale
            root = scene.nodes[0]

            parents = [root]

            while len(parents) > 0:
                parent = parents.pop(0)
                #update here the parent's attribute
                self._read_attributes(parent)

                self.g.node(parent).label = self.gltf.nodes[parent].name

                components = self.gltf.nodes[parent].extras.get("component_roots", [])
                for comp in components:
                    self.g.add_component(parent, comp)

                children = self.gltf.nodes[parent].children

                for child in children:
                    edge_type = self.gltf.nodes[child].extras["edge_type"]
                    self.g.add_child(parent, child, edge_type = edge_type)

                parents.extend(children)


    def _read_geometry(self, scale, tranform = None, vid = None): #read the geometry at scale = scale
        # transform is the global transformation matrix of the parent node
        
        if tranform is None:
            tranform = np.identity(4)
        if vid is None:
            vid = self.g.roots(scale)
        
        for v in vid:
            mesh_id = getattr(self.gltf.nodes[v], "mesh", None)
            if mesh_id is not None:
                ref_geo = self.g[0]["ref_meshes"][mesh_id]
                top = self.gltf.nodes[v].extras.get("top", float('nan'))
                base = self.gltf.nodes[v].extras.get("base", float('nan'))

                if not isnan(top) and not isnan(base):
                    tapered = self.taper_x(top, base, ref_geo)
                else:
                    tapered = ref_geo
                
                # t = self.gltf.nodes[v].translation
                # q = self.gltf.nodes[v].rotation
                # s = np.array(self.gltf.nodes[v].scale)
                # mat = get_matrix4(t, q)
                mat = np.array(self.gltf.nodes[v].matrix).reshape((4,4), order = "F")
                global_mat = tranform@mat

                self.g.node(v).geometry = transformed_from_mat(global_mat, tapered, is_mesh=False)
                self.g.node(v).shapeIndex = mesh_id
                self._read_geometry(scale, global_mat, self.g.children(v))

        self.g.node(0).shapes = [{"meshIndex":i, "materialIndex":0} for i in range(len(self.g[0]["ref_meshes"]))]
        self.g.node(0).materials = dict(zip(range(len(self.g[0]["ref_meshes"])), [pgl.Material.DEFAULT_MATERIAL]*len(self.g[0]["ref_meshes"])))
        
    # def get_transformation(self, vid):
    #     t = self.gltf.nodes[vid].translation
    #     q = self.gltf.nodes[vid].rotation
    #     s = self.gltf.nodes[vid].scale
    #     mat = get_matrix4(t,q,s)

    #     if self.g.parent(vid) is not None:
    #         return self.get_transformation(self.g.parent(vid))@mat
    #     else:
    #         return mat




            
            


            
            

            
            



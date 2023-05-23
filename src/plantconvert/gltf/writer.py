from math import isnan
import base64
from warnings import warn

from openalea.mtg import traversal
import openalea.mtg.mtg as mtg

from . import gltf
import numpy as np

from .. import matrix
from .. import binary_tools
from ..geometry import mat_from_transformed, taper_along_x, tapering_radius_from_transformed


class gltf_builder(object):
    """
    This class is used to build a gltf object from the mtg.
    The gltf object is implemented in pygltflib : 
        A Python library for reading, writing and handling GLTF files.
        link : https://github.com/sergkr/gltflib

    basic usage : 
    
    builder = gltf_builder(g, features = ["Length", "Width"]) 
    # you should initiate an instnace with your mtg g and a list of features to be written in the gltf object.

    builder.build() 
    #by calling this method, the build.gltf object will be created according to the mtg g.

    #Finally, use the gltf's method to output a gltf file
    Here we choose : 

    builder.gltf.save_json("test.gltf") #here we choose to output a simple json file. The meshes are written in an embedded (when we construct the gltf object). You can choose also to output in a more compact file type. Please refer to the pygltflib's documentation

    """

    def __init__(self, g : mtg.MTG, features : list = None):
        """
        Create a new instance of gltf_builder with your mtg and your list of features to be written in the gltf.
        
        """
        
        if not features:
            self.features = []
        else:
            self.features = features

        self.g = g
        
        #property vid is added after using reindex
        # it's a mapping from old vid to the new id 
        self.g.reindex()
        
        self.gltf = gltf.GLTF2()
        self.gltf_meshes = {}

    def build(self):
        """
        Build the gltf object with embedded mesh information.
        Ues the methods implemented in pygltflib to output it into a file of a given type.
        """
        self._add_meshes()
        self._add_topology()
        # validator.validate(self.gltf)

    def _add_meshes(self, meshes = None):
        """
        Process a reference mesh by adding one more buffer
        """
        if meshes is None:
            # get the reference meshes
            ref_meshes = getattr(self.g.node(0), "ref_meshes", None)
            if ref_meshes is None:
                raise ValueError("the mtg doesnot contain reference meshes.")

            if isinstance(ref_meshes, dict):
                meshes = [ref_mesh[0] for ref_mesh in ref_meshes.values()]
                mesh_id = list(ref_meshes.keys())
            elif isinstance(ref_meshes, list):
                meshes = ref_meshes
                mesh_id = range(len(ref_meshes))
            
        for triset, id in zip(meshes, mesh_id):
            points = binary_tools.pack_vec_array(triset.pointList, "float")
            normals = binary_tools.pack_vec_array(triset.normalList, "float")
            try:
                tcoords = binary_tools.pack_vec_array(triset.texCoordList, "float")
            except TypeError:
                tcoords = b""
                warn("No tex coordinates are defined !")
            indices = binary_tools.pack_vec_array(triset.indexList, "ushort")
            
            all_data = points+normals+tcoords+indices
            encoded = str(base64.b64encode(all_data).decode('utf-8'))

            byte_length = len(all_data) 

            #instantiate a buffer and update its value
            buffer = gltf.Buffer()
            buffer.uri = gltf.DATA_URI_HEADER+encoded
            buffer.byteLength = byte_length
            
            # update buffers
            self.gltf.buffers.append(buffer)
            buffer_ind = len(self.gltf.buffers)-1 #get the index of the last added buffer

            # instantiate bufferviews and update their value
            buffer_view_ind = gltf.BufferView() # indices buffer view
            buffer_view_vec3 = gltf.BufferView() # vec 3 buffer view (normals and points)

            if len(tcoords) > 0: # if t coords exist, create the bufferviews
                buffer_view_vec2 = gltf.BufferView() # vec 2 buffer view (tex coord)
                buffer_view_vec2.buffer = buffer_ind
                buffer_view_vec2.byteLength = len(tcoords)
                buffer_view_vec2.byteOffset = len(points)+len(normals)
                buffer_view_vec2.target = gltf.ARRAY_BUFFER
                self.gltf.bufferViews.append(buffer_view_vec2)
                tcoords_ind = len(self.gltf.bufferViews) - 1

            buffer_view_vec3.buffer = buffer_ind
            buffer_view_vec3.byteLength = len(points)+len(normals)
            buffer_view_vec3.byteStride = 12
            buffer_view_vec3.target = gltf.ARRAY_BUFFER



            buffer_view_ind.buffer = buffer_ind
            buffer_view_ind.byteLength = len(indices)
            buffer_view_ind.byteOffset =  len(points)+len(normals)+len(tcoords)
            buffer_view_ind.target = gltf.ELEMENT_ARRAY_BUFFER

            #add bufferviews to the object
            # and keep the buffer view's index
            self.gltf.bufferViews.append(buffer_view_vec3)
            points_ind = len(self.gltf.bufferViews) - 1
            normals_ind = len(self.gltf.bufferViews) - 1
            self.gltf.bufferViews.append(buffer_view_ind)
            indices_ind = len(self.gltf.bufferViews) - 1

            #instantiate accessors
            aces_ind = gltf.Accessor()
            aces_points = gltf.Accessor()
            aces_normals = gltf.Accessor()

            aces_ind.bufferView=indices_ind
            aces_ind.byteOffset = 0
            aces_ind.componentType = gltf.UNSIGNED_SHORT
            aces_ind.count = len(indices)//2
            aces_ind.type = gltf.SCALAR

            aces_points.bufferView = points_ind
            aces_points.byteOffset = 0
            aces_points.componentType = gltf.FLOAT
            aces_points.count = len(points)//(4*3)
            aces_points.type = gltf.VEC3
            min_bounds, max_bounds = triset.pointList.getBounds()
            aces_points.max = list(max_bounds)
            aces_points.min = list(min_bounds)

            aces_normals.bufferView = normals_ind
            aces_normals.byteOffset = len(points)
            aces_normals.componentType = gltf.FLOAT
            aces_normals.count = len(normals)//(4*3)
            aces_normals.type = gltf.VEC3

            if len(tcoords) > 0: #instantiate tcoords accessor only if they exist
                aces_tcoords = gltf.Accessor()
                aces_tcoords.bufferView = tcoords_ind
                aces_tcoords.byteOffset = 0
                aces_tcoords.componentType = gltf.FLOAT
                aces_tcoords.count = len(tcoords)//(4*2)
                aces_tcoords.type = gltf.VEC2
                self.gltf.accessors.append(aces_tcoords)
                tcoords_ind = len(self.gltf.accessors) - 1

            # add all other accessors
            self.gltf.accessors.append(aces_points)
            self.gltf.accessors.append(aces_normals)
            self.gltf.accessors.append(aces_ind)

            n = len(self.gltf.accessors)
            points_ind = n - 3
            normals_ind = n - 2
            indices_ind = n - 1

            mesh = gltf.Mesh()
            primitive = gltf.Primitive()
            primitive.attributes.NORMAL = normals_ind
            primitive.attributes.POSITION = points_ind
            if len(tcoords) > 0:
                primitive.attributes.TEXCOORD_0 = tcoords_ind
            primitive.indices = indices_ind
            primitive.mode = gltf.TRIANGLES

            mesh.primitives.append(primitive)
            self.gltf.meshes.append(mesh)
            self.gltf_meshes[id] = len(self.gltf.meshes) - 1

    def _add_topology(self):
        """
        Translate the mtg into the scene graph of gltf
        """
        iter_mtg = traversal.iter_mtg2(self.g, self.g.root)
        n = len(self.g)

        nodes = [gltf.Node() for i in range(n)]
        
        for vid in iter_mtg:
            parent_id = self.g.parent(vid)

            # set the label
            nodes[vid].name = self.g.label(vid)
        
            # this function add mtg node attribute into the gltf node
            self._add_extra2node(vid, nodes[vid])

            
            # here we solve the topology
            children = self.g.children(vid)
            nodes[vid].children.extend(children)
            nodes[vid].extras["scale"] = self.g.scale(vid)
            nodes[vid].extras["edge_type"] = self.g.edge_type(vid)
            # if the mtg node is not at the finest scale
            nodes[vid].extras["component_roots"] = self.g.component_roots(vid)

            # try to solve geometry
            geo = getattr(self.g.node(vid), "geometry", None)
            shapeIndex = self.g.node(vid).shapeIndex
            parent_geo = getattr(self.g.node(parent_id), "geometry", None)

            if geo is not None:
                mat_c = mat_from_transformed(geo)
                if parent_geo is None:
                    mat_p = None
                else:
                    mat_p = mat_from_transformed(parent_geo)

                try:
                    # translation,rotation,scaling = maths.global_to_local_no_scale(mat_c,mat_p)
                    # translation,rotation,scaling = maths.global_to_local(mat_c,mat_p, use_quaternion=False)
                    # nodes[vid].scale = scaling.tolist()
                    # nodes[vid].rotation = rotation
                    # nodes[vid].translation = translation.tolist()
                    
                    nodes[vid].matrix = matrix.global_to_local_matrix(mat_c, mat_p).flatten("F").tolist()

                    top,base = tapering_radius_from_transformed(geo)

                    if not isnan(top) and not isnan(base):
                        nodes[vid].extras["top"] = top
                        nodes[vid].extras["base"] = base
                    else:
                        warn("nan value found in tapering")

                except ZeroDivisionError:
                    warn("singular matrix found in the mtg, we ignore the geometry of the corresponding node")
                except npl.LinAlgError:
                    warn("singular matrix found in the mtg, we ignore the geometry of the corresponding node")
                except matrix.TRSError:
                    warn("singular matrix found in the mtg, we ignore the geometry of the corresponding node")
                else:
                    mesh_id = self.g[0]["shapes"][shapeIndex]["meshIndex"]
                    mesh_gltf_id = self.gltf_meshes[mesh_id]
                    nodes[vid].mesh=mesh_gltf_id
                    
                # nodes[vid].matrix = list(np.identity(4).flatten())

        self.gltf.nodes = nodes
        for s in self.g.scales_iter():
            scene = gltf.Scene()
            scene.name = "Scene of scale %s"%(s)
            scene.nodes = self.g.roots(s)
            self.gltf.scenes.append(scene)

        self.gltf.scene = s
        

    def _add_extra2node(self,i, gnode : gltf.Node):
        """
        Add the attributes of ith mtg node to a gltf node:
        input : 
        i : the index of the mtg node
        gnode : the gltf node to be updated 
        """
        for f in self.features:
            value = getattr(self.g.node(i), f, None)
            if value is not None:
                gnode.extras[f] = value














        

    
from warnings import warn
from math import isnan,sqrt

from . import ET
from .const import OPF_TYPES

from .. import mtg
from .. import pgl
from ..matrix import *


from .. import geometry

from .. import material


class Unknown_edge_type(Exception):
    pass

def all_empty(last_indices):
    """ Function used in read topology.
    return True if all the stacks are empty """
    return sum((len(last_indices[k]) for k in last_indices)) == 0

class Opf(object):
    """ 
    A read/write topological and geometrical opf format to OpenAlea (mtg and PlantGL)

    The object contains as properties : 
    
    OpfInfo : opf file's information
        
    Meshes : a list of reference meshes. Each mesh is represented by a dictionary (use keys function to get the exact keys) and contains :
            id : the id of the mesh
            points : a list of all nodes coordinates in 3D
            faces : the connectivity table of the mesh
            normal : the normal vectors at each node of the mesh
            textureCoords (optional) : the texture coordinates
            plantgl_obj : the PlantGL object that represents the mesh (TriangleSet)
            
    Materials : a list of materials. Each material is represented by a dictionary and contains :
            id : the id of the material
            emission : a color represented in RGBA format (the first 3 components are float value bounded between 0,1 and should be converted to 0,255 (integer) if required)
            ambient : the same as emission
            diffuse : the same as emission
            specular : the same as emission
            shininess : float bounded between 0 to 128
            plantgl_obj : the PlantGL object that represents the material (Material)
            
    Shapes : a list of shapes. Each shape is represented by a dictionary and contains : 
            id : the id of the shape
            meshIndex : the id of the mesh to create this shape
            materialIndex : the id of the material to create this shape
            
    Attributes : a dictionary of attributes used to describe each organe of the plant. The keys of this dictionary correspond to the name of the attribute while the associated value is a lambda function that convert the data to the correct type
        
    Mtg : an openalea object that reads the topology structure of the plant. The attributes of the mtg are those read previously and geometry that is given by a shape  
    
    Example : 
    parser = Opf("simple_plant.opf")
    parser.build()
    parser.write_mtg("simple_plant.mtg")    
    print(parser.Mtg) """
    
    def __init__(self,OpfPath, verbose = False):
        """ Initialize the parser obj with :
        OpfPath : a path to the opf file that you want to parse
        verbose : a boolean, when it's true more information will be printed on the sreen while parsing the file. The default value is False.
        
        """
        # initialize the iterator
        self._opf_iter=  ET.iterparse(OpfPath, events=("start","end"))
        self._verbose = verbose

        # the first element is known to be opf, we should save the information of the current opf file
        self._event, self._element = self._next()
        self.OpfInfo = self._element.attrib

        # an empty list to store the reference meshes
        # A mesh is represented by :
        #  an object TriangleSet, 
        self.Meshes = {}

        # an empty list to store the reference materials
        # A mesh is represented by object Material
        self.Materials = {}

        # an empty list to store shapes. A shape is a combination of a mesh and a material.
        # A shape is represented by object Shape 
        self.Shapes = {}

        # an empty list to store attributes to describe each node of the Mtg
        self.Attributes = {}

    def read_opf(self):
        """ Once initialized, use this method to perform parsing. This method should be launched at most 1 time. """

        while not(self._event == "end" and self._element.tag == "opf"):
            self._event, self._element = self._next()
            if self._element.tag == "meshBDD":
                self._read_meshBDD()
            elif self._element.tag == "materialBDD":
                self._read_materialBDD()
            elif self._element.tag == "shapeBDD":
                self._read_shapeBDD()
            elif self._element.tag == "attributeBDD":
                self._read_attributeBDD()
            elif self._element.tag == "topology":
                self._read_topology()
        
        return self.Mtg

    def _next(self):
        return next(self._opf_iter)

    def _read_points(self,id):
        #start event should be made outside the method
        self._event, self._element = self._next() # here we receive the end event of the xml node
        temp = self._element.text.split()
        self.Meshes[id]["points"] = []
        for i in range(0,len(temp),3):
            if isnan(float(temp[i])) or isnan(float(temp[i+1])) or isnan(float(temp[i+2])):
                # if NaN value is found in the points, raise an error
                raise ValueError("NaN value is found in the points coordinates")
            self.Meshes[id]["points"].append((float(temp[i]), float(temp[i+1]), float(temp[i+2])))

    def _read_normals(self,id):
        self._event, self._element = self._next()
        temp = self._element.text.split()
        self.Meshes[id]["normals"] = []
        for i in range(0,len(temp),3):
            if isnan(float(temp[i])) or isnan(float(temp[i+1])) or isnan(float(temp[i+2])):
                # if NaN value is found in the normals, rejet that information and let plantgl compute the normals
                self.Meshes[id].pop("normals")
                if self._verbose :
                    warn("NaN value is found in normals of mesh %s. We let plantgl compute the normal vectors "%(id))
                break
            _norm = sqrt(float(temp[i])**2+float(temp[i+1])**2+float(temp[i+2])**2)
            try : 
                self.Meshes[id]["normals"].append((float(temp[i])/_norm, float(temp[i+1])/_norm, float(temp[i+2])/_norm))
            except ZeroDivisionError:
                self.Meshes[id].pop("normals")
                if self._verbose:
                    warn("0 vector is found in normals of mesh %s. We let plantgl compute the normal vectors "%(id))
                break
    def _read_texturecoordinates(self,id):
        self._event, self._element = self._next()
        temp = self._element.text.split()
        self.Meshes[id][self._element.tag]=[(float(temp[i]), float(temp[i+1])) for i in range(0,len(temp),2)]

    def _read_faces(self,id):
        self.Meshes[id]["faces"] = [] 
        while not(self._event == "end" and self._element.tag == "faces"):
            self._event, self._element = self._next() #starting event of face
            if self._event == "end" and self._element.tag == "face":
                face = self._element.text.split()
                self.Meshes[id]["faces"].append((int(face[0]), int(face[1]), int(face[2])))

    def _read_mesh(self):
        self._event, self._element = self._next()
        if self._element.tag == "meshBDD":
            # end of reading
            pass
        else:
            #save the information of the mesh
            mesh_attribute = self._element.attrib
            id = int(mesh_attribute.pop("Id"))

            self.Meshes[id] = mesh_attribute
            self.Meshes[id]['enableScale'] = self.Meshes[id]['enableScale'].lower() == "true"
            # print(self.Meshes)
            while not(self._event == "end" and self._element.tag == "mesh"):
                self._event, self._element = self._next()
                if self._element.tag == "points":
                    #read the coordinates of points
                    self._read_points(id)
                elif self._element.tag == "normals":
                    #read the normal vectors
                    self._read_normals(id)
                elif self._element.tag == "textureCoords":
                    #read the texture coordinates
                    self._read_texturecoordinates(id)
                elif self._element.tag == "faces":
                    #read the connectivity table
                    self._read_faces(id)
            self._message("\t one mesh parsed")
            # now construct the TriangSet obj
            self.Meshes[id]['plantgl_obj'] = pgl.TriangleSet(
                self.Meshes[id]["points"],
                self.Meshes[id]["faces"])

            if "normals" in self.Meshes[id].keys():
                self.Meshes[id]['plantgl_obj'].normalList = self.Meshes[id]["normals"]
                self.Meshes[id]["plantgl_obj"].normalPerVertex = True
            else:
                self.Meshes[id]["plantgl_obj"].computeNormalList()
            if "textureCoords" in self.Meshes[id].keys():
                self.Meshes[id]['plantgl_obj'].texCoordList=self.Meshes[id]["textureCoords"]
                self.Meshes[id]['plantgl_obj'].texCoordIndexList=self.Meshes[id]["faces"]

    def _read_meshBDD(self):
        #self._event, self._element = self._next()
        self._message("start parsing meshes")

        while not(self._event == "end" and self._element.tag == "meshBDD"):
            self._read_mesh()

        # sort the meshes by ID
        self.MeshesNb = len(self.Meshes)
        self._taper = geometry.taper_along_x([self.Meshes[id]['plantgl_obj'] for id in self.Meshes])
        self._message("end parsing meshes")

    def _read_material(self):
        self._event, self._element = self._next()
        if self._element.tag == "materialBDD":
            # end parsing materials
            pass
        else:
            # it was the starting event of one material
            id = int(self._element.attrib['Id'])
            self.Materials[id] = {}
            while not(self._event == "end" and self._element.tag == "material" ): 
                if self._event == "end":
                    text = self._element.text.split() 
                    self.Materials[id][self._element.tag] = [float(t) for t in text]
                self._event, self._element = self._next()
            #save shininess as a float
            self.Materials[id]["shininess"]=self.Materials[id]["shininess"][0]
            # convert the Material to plantgl object

            self.Materials[id]["plantgl_obj"] = material.toplantgl(self.Materials[id])

            self._message("\t one material parsed")
    
    def _read_materialBDD(self):
        #self._event, self._element = self._next()
        self._message("start parsing materials")
        while not(self._event == "end" and self._element.tag == "materialBDD"):
            self._read_material()

        # print(self.Materials)
        self.MaterialsNb = len(self.Materials)
        self._message("end parsing materials")

    def _read_shape(self):
        self._event, self._element = self._next()
        if self._element.tag == "shapeBDD":
            # end parsing shape
            pass
        else:
            # starting event of one shape
            id = int(self._element.attrib['Id'])
            self.Shapes[id] = {}
            while not(self._event == "end" and self._element.tag == "shape"):
                if self._event == "end":
                    if self._element.text.isnumeric():
                        self.Shapes[id][self._element.tag] = int(self._element.text)
                    else:
                        self.Shapes[id][self._element.tag] = self._element.text 
                self._event, self._element = self._next()
            self._message("\t one shape parsed")

    def _read_shapeBDD(self):
        self._message("start parsing shapes")
        #self._event, self._element = self._next()
        while not(self._event == "end" and self._element.tag == "shapeBDD"):
            self._read_shape()
        self.ShapesNb = len(self.Shapes)
        self._message("end parsing shapes")

    def _read_attributeBDD(self):
        self._message("start parsing attributes")

        #self._event, self._element = self._next()
        while not(self._event == "end" and self._element.tag == "attributeBDD"):
            self._event, self._element = self._next()
            if self._element.tag == "attributeBDD":
                pass
            else:
                if self._event == "start":
                    _name = self._element.attrib['name']
                    _type = list(OPF_TYPES[self._element.attrib['class']])
                    _type.append(self._element.attrib['class'])
                    self.Attributes[_name] = _type
                    self._message("\t one attribute parsed")
        self._message("end parsing attributes")

    def _read_geometry(self,i):
        while not(self._event == "end" and self._element.tag == "geometry"):
            self._event, self._element = self._next()
            if self._event == "end":
                if self._element.tag == "shapeIndex":
                    shape_index = int(self._element.text)
                elif self._element.tag == "mat":
                    temp = self._element.text.split()
                    mat = np.array([float(t) for t in temp]).reshape(3,4)
                    # m = mat[:3,:3].T@mat[:3,:3]

                    # if not np.all(np.isclose(m , np.diag(np.diagonal(m)))):
                    #     print(i)
                    #     print(m)
                elif self._element.tag == "dUp":
                    up = float(self._element.text)
                elif self._element.tag == "dDwn":
                    dwn = float(self._element.text)
        try:
            #try to create the shape object (transformed geometry + material)
            #in which case shape_index should exist
            mesh_index = self.Shapes[shape_index]["meshIndex"]
            material_index = self.Shapes[shape_index]["materialIndex"]
        except NameError:
            pass # no shape is assigned to the mtg node
        else:

            geo = self.Meshes[mesh_index]['plantgl_obj']
            enable_scale = self.Meshes[mesh_index]['enableScale']
            material = self.Materials[material_index]['plantgl_obj']
            # print(self.Mtg[i]['label'])
            # print("enable scale ? %s"%(enable_scale))

            if enable_scale and not( isnan(up) or isnan(dwn)):
                # find a way to perform tapering along x axis
                geo = self._taper(up,dwn,geo)

            geo = geometry.transformed_from_mat(mat,geo,is_mesh=False) #rotate and scale
            
            #now combine the geometry object and material to create shape
            shape = pgl.Shape(geo,material)
            shape.id = i
            #now add shape to the corresponding property of node i:

            setattr(self.Mtg.node(i), "geometry", shape)
            setattr(self.Mtg.node(i), "shapeIndex", shape_index)
            setattr(self.Mtg.node(i), "meshIndex", mesh_index)
            setattr(self.Mtg.node(i), "materialIndex", material_index)

    def _read_nodal_attribute(self,i):
        # add information to i-th node of the Mtg
        tag = self._element.tag

        if tag == "geometry": #geometry contains simple sub-nodes
            self._read_geometry(i)
        
        else:
            # other information is store in simple node
            # by invoking self._next we obtain the ending event of the node
            self._event, self._element = self._next()
            tag = self._element.tag # attribute name
            text = self._element.text # attribute value
            conversion_func = self.Attributes[tag][0] # lambda function that convert value into the correct type
            setattr(self.Mtg.node(i), tag, conversion_func(text))
            
    def _read_topology(self):
        #create the scene, knowing that the starting event of topology is made outside the function
        self.Mtg = mtg.MTG()

        # add properties to the Mtg (given by self.Attributes)
        for k in self.Attributes.keys():
            self.Mtg.add_property(k)
        self.Mtg.add_property('geometry')
        self.Mtg.add_property('shapeIndex')
        self.Mtg.add_property('meshIndex')
        self.Mtg.add_property('materialIndex')
        self.Mtg.add_property('ref_meshes')
        self.Mtg.add_property('materials')
        self.Mtg.add_property('shapes')
        self.Mtg.add_property("user_attributes")
        self.Mtg.add_property("opf_info")
        # the first node (topology) of opf could start with individual
        # if it's the case then we should add the individual manually as openalea.mtg always starts with scene

        label = self._element.attrib['class']
        id = int(self._element.attrib['id'])
        scale = int(self._element.attrib['scale'])
        if scale != 0:
            i = self.Mtg.add_component(self.Mtg.root, component_id = id, label=self._element.attrib['class'])
            parent = {0:0,scale:i}
        else:
            i = self.Mtg.root
            self.Mtg.node(i).label = self._element.attrib['class']
            parent = {scale:i}
        root = self.Mtg.root
        
        self.Mtg.node(root).ref_meshes = dict([(id, (self.Meshes[id]['plantgl_obj'],self.Meshes[id]['enableScale'])) for id in self.Meshes])
        self.Mtg.node(root).materials = dict([(id, self.Materials[id]['plantgl_obj']) for id in self.Materials])
        self.Mtg.node(root).shapes = self.Shapes
        self.Mtg.node(root).user_attributes = self.Attributes
        self.Mtg.node(root).opf_info = self.OpfInfo
        
        last_indices = {scale:[i]} #stacks to track the history of added nodes 
        while not(all_empty(last_indices))>0:
            self._event, self._element = self._next() 
            
            if not(self._element.tag in ["topology","decomp","follow","branch"]):
                # the xml node contains attribute of the current Mtg node
                # add information in the last added node
                self._read_nodal_attribute(parent[scale])
            
            else:                
                #print(last_indices)
                # the xml node contains topological information

                # get the scale of the current node
                scale = int(self._element.attrib['scale'])
                
                if self._event == "end":
                    # ending event
                    i = last_indices[scale].pop(-1)
                    if self._element.tag == "follow":
                        parent[scale] = i #when a follow closed, next node should be added over the last node
                    elif self._element.tag == "branch":
                        parent[scale] = self.Mtg.parent(i) #when a branch closed, next node is added after the parent of the last node

                        #update the finer scale too !
                        try:
                            first_comp = self.Mtg.components(i)[0]
                        except IndexError:
                            pass
                        else:
                            parent[scale+1] = self.Mtg.parent(first_comp)
                    else:
                        parent[scale] = i

                else:
                    # starting event => add node in the Mtg
                    # distinguish the type of connection
                    tag = self._element.tag
                    label = self._element.attrib['class']
                    id = int(self._element.attrib['id'])

                    # if id == 8:
                    #     print(last_indices)
                    #     print(parent)
                    #     print(scale)

                    if tag == "decomp":
                        comp = self.Mtg.add_component(parent[scale-1],component_id=id,label=label)

                        try:
                            last_indices[scale].append(comp)
                        except KeyError: #it's in fact the first node of the current scale
                            last_indices[scale] = [comp]
                        else:
                            # if the complexe has an edge type, the current component should inherit the edge type to previous node of the same scale
                            
                            edge_type = self.Mtg.edge_type(parent[scale-1])

                            if edge_type != "":
                                self.Mtg.add_child(parent=parent[scale],child = comp, edge_type=edge_type)
                        finally:
                            parent[scale] = comp

                    else:
                        if tag == "follow":
                            edge_type = "<"
                        else:
                            edge_type = "+"
                        
                        try : # if not branching or following on the void 
                            parent[scale] = self.Mtg.add_child(parent=parent[scale],child=id,label=label,edge_type=edge_type)
                            last_indices[scale].append(parent[scale])
                        except KeyError:
                            parent[scale] = self.Mtg.add_component(complex_id= parent[scale-1], component_id= id, label = label)
                            last_indices[scale] = [parent[scale]]
                        
                     
    def _message(self,msg):
        if self._verbose:
            print(msg)

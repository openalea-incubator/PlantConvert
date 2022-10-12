
from xml.etree import ElementTree as ET
from xml.dom import minidom
from math import pi
import re

import openalea.mtg as mtg

from .__init__ import float_to_string
from .. import pgl
from .. import geometry

def write_opf(g, filename, features = None):
    """ Write the opf file from the given MTG
    Inputs :

    g : an openalea.mtg object.
    filename : the file where the outputs will be saved.
     """
    if hasattr(g.node(g.root), "opf_info"):
        opf_info = g[0]['opf_info']
    else:
        opf_info = {"version":"2.0","editable":"true"}

    root = ET.Element("opf",opf_info)

    if hasattr(g.node(g.root), "ref_meshes"):
        meshBDD = ET.SubElement(root, "meshBDD")
        _write_meshBDD(g, meshBDD)
    
    if hasattr(g.node(g.root), "materials"):
        materialBDD = ET.SubElement(root, "materialBDD")
        _write_materialBDD(g, materialBDD)
    
    if hasattr(g.node(g.root), "shapes"):
        shapeBDD = ET.SubElement(root, "shapeBDD")
        _write_shapeBDD(g, shapeBDD)

    if features is None: # there is no given features list
        if hasattr(g.node(g.root), "user_attributes"): #try if feature list is given internally
            user_attributes = dict([(key, g[0]["user_attributes"][key][2]) for key in g[0]["user_attributes"]])
            attributeBDD = ET.SubElement(root, "attributeBDD")
            _write_attributeBDD(attributeBDD,user_attributes=user_attributes)
        else: #don't write any features
            user_attributes = dict()
    else:
        if len(features) > 0:
            user_attributes = features
            attributeBDD = ET.SubElement(root, "attributeBDD")
            _write_attributeBDD(attributeBDD, user_attributes=user_attributes)
        else:
            user_attributes = dict()
    topology = ET.SubElement(root, "topology",attrib=_get_xml_attribute(g,g.root))
    _write_topology(g,topology,features=user_attributes)

    text = ET.tostring(root,encoding="UTF-8")
    dom = minidom.parseString(text)
    with open(filename,"wb") as f:
        f.write(dom.toprettyxml(indent='\t',encoding="UTF-8"))

def _vector_array_to_string(vec,level=0):
    #convert an array to a raw string
    #add level times identation in the begging
    text = ""
    for v in vec:
        text += "\t".join([str(value) for value in v]) + "\t"
    return "\n"+"\t"*(level+1) + text + "\n" + "\t"*level

def _write_mesh(tr,mesh):
    # write the points list
    points = ET.SubElement(mesh,"points")
    points.text = _vector_array_to_string(tr.pointList,3)
    #write the the normal vectors
    normals = ET.SubElement(mesh, "normals")
    normals.text = _vector_array_to_string(tr.normalList,3)
    #write the texture coordinates if exist
    if not(tr.texCoordList is None):
        texture = ET.SubElement(mesh, "textureCoords")
        texture.text = _vector_array_to_string(tr.texCoordList,3)
    #write the connectivity table
    faces = ET.SubElement(mesh,"faces")
    for id,f in enumerate(tr.indexList):
        face = ET.SubElement(faces,"face",{"Id":str(id)})
        face.text = "\n"+"\t"*5+"%s %s %s" %(f[0],f[1],f[2])+"\n"+"\t"*4

def _color3_to_RGBA_opf(color,alpha):
    #convert a Color3 object to an array with 4 elements (color + alpha)
    return [str(color.red/255.), str(color.green/255.), str(color.blue/255.)] + [str(alpha)]

def _write_materialBDD(g,materialBDD):
    materials = g[0]["materials"]
    for material_id in materials:
        material = materials[material_id]
        alpha = 1 - material.transparency
        mat = ET.SubElement(materialBDD,"material",{"Id":str(material_id)})

        emi = ET.SubElement(mat, "emission")
        emi.text = "\t".join(_color3_to_RGBA_opf(material.emission,alpha))
        
        amb = ET.SubElement(mat, "ambient")
        amb.text = "\t".join(_color3_to_RGBA_opf(material.ambient,alpha))
        dif = ET.SubElement(mat, "diffuse")
        dif_vec = _color3_to_RGBA_opf(material.ambient,alpha)
        for i in range(3):
            dif_vec[i] = str(material.diffuse * float(dif_vec[i]))
        dif.text = "\t".join(dif_vec)
        spec = ET.SubElement(mat, "specular")
        spec.text = "\t".join(_color3_to_RGBA_opf(material.specular,alpha))
        shininess = ET.SubElement(mat, "shininess")
        shininess.text = str(128.*material.shininess)

def _write_meshBDD(g,meshBDD):
    ref_meshes = g[0]["ref_meshes"]
    nb_meshes = len(ref_meshes)
    if isinstance(ref_meshes, list):
        #make ref_meshes into a dictionary
        ref_meshes = dict(zip(range(nb_meshes), zip(ref_meshes, [True]*nb_meshes)))

    for id in ref_meshes:
        tr,enableScale = ref_meshes[id]
        attribute = {"name":"","shape":"","Id":str(id),"enableScale":str(enableScale).lower()}
        mesh = ET.SubElement(meshBDD, "mesh",attribute)
        _write_mesh(tr,mesh)

def _write_shapeBDD(g,shapeBDD):
    shapes = g[0]["shapes"]
    if isinstance(shapes, list):
        shapes = dict(zip(range(len(shapes)), shapes))
    for id in shapes:
        sh = ET.SubElement(shapeBDD, "shape", {"Id":str(id)})
        if not shapes[id].get("name"):
            node = ET.SubElement(sh, "name")
            node.text = " Mesh%d"%(id)
        for key in shapes[id]:
            node = ET.SubElement(sh, key)
            node.text = str(shapes[id][key])

def _write_attributeBDD(attributeBDD, user_attributes):
    for key in user_attributes:
        ET.SubElement(attributeBDD, "attribute", {"name":key,"class":user_attributes[key]})

def _write_info(g, node, v, features = None):
    if features is None:
        try:
            user_attributes = g[0]['user_attributes']
        except KeyError:
            user_attributes = []
    else:
        user_attributes = features
    for k in user_attributes:
        try:
            text = str(g[v][k])
            info_node = ET.SubElement(node, k)
            info_node.text = text
        except KeyError:
            pass

    try:
        # try if the current node is associated with a geometry
        # then a shape index should be given
        shapeIndex = g[v]["shapeIndex"]
    except KeyError: # no such key, do nothing
        pass
    else: #no exception then add the geometry
        geometry_node = ET.SubElement(node, "geometry", attrib={"class":"Mesh"})
        shape_node = ET.SubElement(geometry_node, "shapeIndex")
        shape_node.text = str(shapeIndex)

        mat = geometry.mat_from_transformed(g[v]['geometry'])
        mat_node = ET.SubElement(geometry_node, "mat")
        
        mat_str ="\n"+"".join(["\t".join([str(mat[i,j]) for j in range(4)])+"\n" for i in range(3)])
        mat_node.text = mat_str
        
        up,down = geometry.tapering_radius_from_transformed(g[v]["geometry"])
        up_node = ET.SubElement(geometry_node,"dUp")
        up_node.text = float_to_string(up)
        down_node = ET.SubElement(geometry_node, "dDwn")
        down_node.text = float_to_string(down)

def _get_xml_attribute(g,v):
    label = g[v].get("label")
    if label is None:
        if v == g.root:
            label = "Scene"
        else:
            raise ValueError("No label defined for the mtg node %d"%(v))
    return {"class":re.sub(r"\d+","",label),"scale":str(g.scale(v)),"id":str(v)}

def _write_topology(g, parent_in, child_in = None, v = None, features = None,visited = None):
    #Recursive function.

    # parent_in is the xml node of mtg node v's parent
    # child_in is the xml node of mtg node v

    # if mtg node w is v's child with edge type follow,
    # w's xml node is in fact a child node of parent_in

    # otherwise, if w is v's branch child,
    # w's xml node is a child node of child_in

    # The mtg nodes should be added in the opf such that : 
    # parent before child, complex before component
    if v is None: # initialization
        v = g.root
    if child_in is None:
        child = parent_in
    else:
        child = child_in

    if visited is None:
        visited = {}

    parent = parent_in
    
    _write_info(g, child, v, features)

    for w in g.component_roots(v): # root of disjoint component trees
        
        visited[w] = True
        attrib = _get_xml_attribute(g,w)
        
        child_next = ET.SubElement(child, "decomp", attrib) 
        _write_topology(g,parent_in=child,child_in=child_next,v=w,features=features,visited=visited)
        
    
     # I should now add all the children of v into the xml object
    for w in g.children(v):
        if not visited.get(w):
            complex_w = w
            complex_v = v

            #go to the first complex of w that is component to v and w's first common complex
            while g.complex(complex_w) != g.complex(complex_v):
                complex_w = g.complex(complex_w)
                complex_v = g.complex(complex_v)

            visited[complex_w] = True
            attrib = _get_xml_attribute(g,complex_w)
            if g.edge_type(w) == "+":
                    #add sub node to v's xml node
                parent_next = child # v's xml node <=> w's parent's xml node
                child_next = ET.SubElement(child,"branch",attrib) # w's xml node
                _write_topology(g, parent_next, child_next, complex_w,features=features,visited=visited)
            else:
                #add sub node to v's parent's xml node
                child = ET.SubElement(parent, "follow", attrib)
                _write_topology(g,parent, child, complex_w,features, visited=visited)                 
    
#----------------------------------------------------------------------------

# This is a fail attempt to extract reference meshes from a list of shapes
# the two functions _extract_ref_.. and _extract_mate... are infact generator (yield key world)
# So you can use next(_extract_...) to get the next value of the function while conserving the internal state of the function

# the idea is, when receiving a shape object, we look into the deepest geometric primitive (a shape is a chained list of transformation and end to a geometric primitive) and compute the overall transformatoin



def _deep_primitive(geo):
    if isinstance(geo, pgl.Transformed) or isinstance(geo, pgl.Shape):
        return _deep_primitive(geo.geometry)
    else:
        return geo.__class__.__name__, geo

def _extract_ref_meshes(shapes):
    ref_meshes = {}
    meshIndex = {}
    enableScale = {}
    for s in shapes:
        geo_name,geo = _deep_primitive(s)
        if not ref_meshes.get(geo_name):
            if geo_name == "Frustum":
                ref_meshes[geo_name] = pgl.tesselate(pgl.EulerRotated(0., pi/2, 0., pgl.Cylinder(radius = 1.))) # the plantgl object furstum is oriented along the z axis while in opf we should save the reference mesh that is oriented along the x axis.
                # we apply a rotation around y of angle pi/2, the reference mesh is thus oriented along x axis. 
                # The radius is set to be 1 to facilitate the tapering and the scaling
                # The default height of the cylinder is 1.
                meshIndex[geo_name] = len(ref_meshes) - 1
                enableScale[geo_name] = True
                ref_meshes[geo_name].computeNormalList()
                key = geo_name
            elif geo_name == "Cylinder":
                ref_meshes[geo_name] = pgl.tesselate(pgl.EulerRotated(0., pi/2, 0., pgl.Cylinder(radius = 1.)))
                meshIndex[geo_name] = len(ref_meshes) - 1
                enableScale[geo_name] = False
                ref_meshes[geo_name].computeNormalList()
                key = geo_name
            elif geo_name == "TriangleSet":
                pgl_id = geo.getPglId()
                ref_meshes[pgl_id] = geo
                meshIndex[pgl_id] = len(ref_meshes) - 1
                enableScale[pgl_id] = False
                ref_meshes[pgl_id].computeNormalList()
                key = pgl_id

        yield ref_meshes[key], meshIndex[key], enableScale[key]

def _extract_materials(shapes):
    materials = {}
    materialIndex = {}
    for s in shapes:
        ap = s.appearance
        color_name = ap.name
        if not materials.get(color_name):
            materials[color_name] = ap
            materialIndex[color_name] = len(materials) - 1
        yield materials[color_name],materialIndex[color_name]


# self.Mtg.add_property('geometry')
# self.Mtg.add_property('shapeIndex')
# self.Mtg.add_property('meshIndex')
# self.Mtg.add_property('materialIndex')
# self.Mtg.add_property('ref_meshes')
# self.Mtg.add_property('materials')
# self.Mtg.add_property('shapes')

def apply_scene(g, scene):
    """
    Add a scene to the mtg. The scene should the support the method : scene.todict() which will return a dictionary with vid as keys and the vertex's geometry as value.

    In order to allow this behavior, when you define your scene from a mtg, for each shape of the scene, you should set id to be vid : 
    shape.id = vid and then you combine the shapes to create your scene.

    This function will also try to extract reference meshes and materials from the given scene (implementation is not complete yet !). But it works when each mtg node has exactly one geometric object associated if it has.

    input : 
    g : a mtg objecty
    scene : a plantgl object 
    """
    property_names = ["geometry","shapeIndex","meshIndex","materialIndex","ref_meshes","materials","shapes"]
    for name in property_names:
        g.add_property(name)

    # create a dictionnary that associate each vertex with this shape
    # sd = {vid : shapelist}, a vertex could be associated with more than 1 shapes
    if isinstance(scene, pgl.Scene):
        sd = scene.todict()
        shapes = [s[0] for s in sd.values()]
    elif isinstance(scene, dict):
        sd = scene
        shapes = list(scene.values())
    else:
        raise TypeError("This type is not recognized !")
    # create a generator of shapes, a vertex can have more than 1 shape
    # for instance let's just take the first one
    

    # get the root id of the mtg
    root = g.root
    g.node(root).ref_meshes = {}
    g.node(root).materials = {}
    g.node(root).shapes = {}
    get_key = lambda d,x : list(d.keys())[list(d.values()).index(x)]
    ref_meshes = _extract_ref_meshes(shapes)
    materials = _extract_materials(shapes)

    # get tapered_x object : 
    Tapered_opf = geometry.taper_along_x()

    for vid,sh in zip(sd.keys(), shapes):
        try:
            mesh, meshIndex, enableScale =  next(ref_meshes)
        except ValueError:
            material, materialIndex = next(materials)
            continue
        except StopIteration:
            print(vid)
            raise StopIteration
        material, materialIndex = next(materials)

        # ----------------- update the global properties -----------------
        # if discover a new mesh : 
        if not meshIndex in g.node(root).ref_meshes.keys():
            g.node(root).ref_meshes[meshIndex] = (mesh, enableScale)
        # if discover a new material : 
        if not materialIndex in g.node(root).materials.keys():
             g.node(root).materials[materialIndex] = material
        
        # if discover a new shape ( an association of a material index and a mesh index)
        d = {"meshIndex":meshIndex,"materialIndex":materialIndex}
        
        try : 
            shapeIndex = get_key(g.node(root).shapes, d)
        except ValueError: #d is not in the shape list
            g.node(root).shapes[len(g.node(root).shapes)] = d
            shapeIndex = len(g.node(root).shapes)-1

        #------------------ update the geometry information of the vertex
        geo_name, geo = _deep_primitive(sh)

        if geo_name == "Frustum":
            base = geo.radius
            top = geo.radius*geo.taper
            height = geo.height
            tap = Tapered_opf(top, base, mesh)
            
            mat = pgl.Matrix4(pgl.Matrix3(0.,0.,1.,0.,1.,0.,1.,0.,0.))*pgl.Matrix4(pgl.Matrix3(height,0.,0.,0.,1.,0.,0.,0.,1.))
            # the transformation matrix of sh is made with assumption that the reference geometry object is oriented along the z axis.
            # Before applying it we should orient the Tapered object along z axis (it's by default in opf that is oriented along x axis)
            # Similarly the scaling is applied along x axis first ! 
            mat =  geometry.mat_from_transformed(sh) * mat

            final_geo = geometry.transformed_from_mat(mat, tap,is_mesh=False)
        elif geo_name == "Cylinder":
            radius = geo.radius
            height = geo.height
            mat =pgl.Matrix4(pgl.Matrix3(0.,0.,1.,0.,1.,0.,1.,0.,0.))*pgl.Matrix4(pgl.Matrix3(height,0.,0.,0.,radius,0.,0.,0.,radius))
            mat =  geometry.mat_from_transformed(sh) * mat

            final_geo = geometry .transformed_from_mat(mat, mesh, is_mesh=False)
        elif geo_name == "TriangleSet":
            final_geo = geo
        else:
            raise NotImplementedError("This geometry is not supported yet : %s"%(geo_name))

        # add geometry to vid : 
        g.node(vid).shapeIndex = shapeIndex
        g.node(vid).geometry = final_geo
        g.node(vid).meshIndex = meshIndex
        g.node(vid).materialIndex = materialIndex

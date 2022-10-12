from math import pi

from . import np
from . import npl

from . import pgl
from . import mtg

from .matrix import mat4_to_numpy, TRS_from_matrix4

#TODO:
# move the implementation of opf parser here : 
# 1. taper along x axis (find a better for the class) ok, 
# 2. transformed  from mat
# 3. mat from transformed
# 4. tapering radius
# 5. get scene


# a class to apply tapering along x axis (in opf the tapering is along z axis)
class taper_along_x(object):
    """ 
    A callable class to perform tapering along x axis

    To initialize this class with a list of reference meshes (represented by TriangleSet)

    If the given mesh is not in the list then it will be added
    """

    def __init__(self, ref_meshes=None):


        if ref_meshes is None:
            self.rotated_ref_meshes = {}
            return
        
        self.rotated_ref_meshes = dict([(tr.getPglId(),pgl.tesselate(pgl.EulerRotated(0.,-pi/2,0.,tr)) ) for tr in ref_meshes])
        

    def __call__(self, up, down, mesh):
        pgl_id = mesh.getPglId() #mesh is supposed to be one of the reference meshes

        #get the rotated mesh and taper it with up/down
        try:
            rotated = self.rotated_ref_meshes[pgl_id]
        except KeyError : 
            #
            rotated = pgl.tesselate(pgl.EulerRotated(0.,-pi/2,0.,mesh))
            self.rotated_ref_meshes[pgl_id] = rotated

        tapered = pgl.Tapered(down,up,rotated) #proceed the tapering
        tapered = pgl.EulerRotated(0., pi/2, 0., tapered)

        return tapered

def transformed_from_mat(A, geo, is_mesh = False):
    """ Apply the transformation A (a 3 by 4 matrix) on the geometry
    return the transformed geometry.
    
    Inputs : 
    A : a 3 by 4 numpy array that describes the transformation in the reference of the scene. This matrix is supposed to be TRS decomposible
    geo : a geometry object from PlantGL
    is_scaled : a boolean, if true the scaling part of A will be applied. By defaut is true. It's not used and should be kept True
    is_mesh : a boolean, if true a new mesh (TriangleSet) will be created. Otherwise we only create a geometry object (no duplication of mesh in the memory)

    outputs :
    Transformed geometry. if is_mesh then we get a new mesh otherwise we only create a geometry object     """
    # return the transformed geometry object, the transformation is described by the 3 by 4 matrix A.
    # we perform the Qr transformation of A, so that A = Q*r where:
    # Q is a unity matrix and r is upper-triangular. To use the oriented object of plantgl, Q should have positive determinant
    # r is in our case diagonal since A is a composition of rotations and scaling
    if is_mesh:
        # 1. get the geometric mesh
        # 2. Create a Matrix3 or Matrix4
        # 3. Apply the Matrix to the pointList
        # 4. Modify the mesh with the new pointList
        if isinstance(geo, pgl.Tapered):
            mesh = pgl.tesselate(geo)
        else:
            mesh = geo.deepcopy()
        n = len(mesh.pointList)

        M = pgl.Matrix4(*A.T.tolist())
        for i in range(n):
            mesh.pointList[i] = M*mesh.pointList[i]
        mesh.computeNormalList()
        return mesh
    else:
        if isinstance(A, pgl.Matrix4):
            A_np = mat4_to_numpy(A)
            # print(A_np)
        else:
            A_np = A

        t,Q,s = TRS_from_matrix4(A_np)
        return pgl.Translated(*t.tolist(), pgl.Oriented(Q[:,0],Q[:,1],pgl.Scaled(s.tolist(),geo)))

def mat_from_transformed(geo):
    """ Get the global transformation matrix from a transformed geometry 
     """
    
    #the identity matrix : 
    ID = pgl.Matrix4(*[pgl.Vector4([1.*(j==i) for j in range(4)]) for i in range(4)])
    try:
        if isinstance(geo, pgl.EulerRotated): #geo is the output of tapered_opf
            return ID
        elif isinstance(geo, pgl.TriangleSet): #geo has not been tapered 
            return ID
        elif isinstance(geo, pgl.Frustum):
            return ID
        elif isinstance(geo, pgl.Cylinder):
            return ID
        elif isinstance(geo, pgl.Shape):
            return mat_from_transformed(geo.geometry)
        elif isinstance(geo, pgl.Translated):
            mat = geo.transformation().getMatrix()
            return mat * mat_from_transformed(geo.geometry)
        elif isinstance(geo, pgl.Oriented):
            mat = geo.transformation().getMatrix()
            return mat * mat_from_transformed(geo.geometry)
        elif isinstance(geo, pgl.Scaled):
            mat = geo.transformation().getMatrix()
            return mat * mat_from_transformed(geo.geometry)
        else:
            raise TypeError("input geometry's type is not recognized : %s"%(type(geo)))
    except TypeError:
        raise TypeError("input geometry's type is not recognized : %s"%(type(geo)))

def tapering_radius_from_transformed(geo):
    """Get the tapering radii from the input geometry.
    """

    if isinstance(geo, pgl.TriangleSet):
        return float('nan'),float('nan')
    elif isinstance(geo, pgl.Tapered):
        return geo.topRadius, geo.baseRadius
    else:
        return tapering_radius_from_transformed(geo.geometry) 

def get_scene(g : mtg.MTG, filter = None):
    """
    This method traverses the mtg g and reads the geometry property of the nodes that are allowed by the filter. It creates a plantgl Scene object of all geometric objects combined.
    """
    if filter is None:
        # if no filter given then return all the nodes
        filter = lambda g,v : True

    shape_list = []
    
    for v in g:
        try:
            if filter(g,v):
                geo = g[v]["geometry"]
                if isinstance(geo, pgl.Shape):
                    geo.id = v
                elif isinstance(geo, pgl.Geometry):
                    geo = pgl.Shape(geo, pgl.Material.DEFAULT_MATERIAL)
                    geo.id = v
                shape_list.append(geo)
        except KeyError:
            pass
    return pgl.Scene(shape_list)
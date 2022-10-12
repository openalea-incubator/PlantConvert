from pygltflib import Material
import vtkmodules.all as vtk
from . import pgl

def toplantgl(material_data):
    """ Create a plantgl object to represent a material from the input material_data.
    The input should be a dictionary that contains exactly : 
    An Id,
    4 colors in RGBA : emission, ambient, diffuse and specular.
    shininess value
    
    It returns a plantgl.Material object (it's not exactly the same, some information will be lost for example, the alpha value in opf is defined for each color (emission, etc. ) while in plantgl there is only a global alpha value : transparency = 1 - alpha) """
    #return a plantgl object : material that corresponds to the input dictionary
    if set(material_data.keys()) != {'emission','ambient','diffuse','specular','shininess'}:
        raise KeyError
    n = len(material_data)
    #compute the transparency
    #initialize a plantgl material object
    shininess = material_data['shininess']/128.
    
    # transparency = min([1.-material_data['emission'][-1], 1.-material_data['ambient'][-1] , 1.-material_data['specular'][-1]]) # revert alpha to build transparency
    transparency = 0
    emission = pgl.Color3(*[int(255*material_data['emission'][i]) for i in range(3)])
    ambient = pgl.Color3(*[int(255*material_data['ambient'][i]) for i in range(3)])
    specular = pgl.Color3(*[int(255*material_data['specular'][i]) for i in range(3)])
    diffuse_over_ambient = [material_data['diffuse'][i]/material_data['ambient'][i] for i in range(3) if material_data['ambient'][i]!=0.]
    try:
        diffuse = sum(diffuse_over_ambient)/len(diffuse_over_ambient)
    except ZeroDivisionError:
        diffuse = 0.
    return pgl.Material(ambient=ambient, diffuse=diffuse, specular=specular,emission=emission,shininess=shininess,transparency = transparency)

def togltf(material_data):
    """
    Create the material information accepted by GLTF, not implemented yet
    """

    raise NotImplementedError


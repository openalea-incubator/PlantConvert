import vtkmodules.all as vtk

from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.util import numpy_support as nps

import openalea.plantgl.all as pgl
from openalea.mtg.algo import traversal
import os
import numpy as np
from warnings import warn
import re

def _pgl_pointarray_to_np(points, **kwargs):
    n = len(points)
    m = len(points[0])
    
    data_type = kwargs.get("dtype", np.float32)

    points_np = np.empty((n,m), dtype=data_type)
    for i,v in enumerate(points):
        points_np[i,:] = v
    return points_np


def ugrid_from_plantgl(geo_pgl):
    """
    Create an ugrid vtk object equivalent to a plantgl geometry object.
    Tesselation is applied.
    """

    if isinstance(geo_pgl, pgl.TriangleSet):
        triset = geo_pgl
    elif isinstance(geo_pgl, pgl.Shape):
        triset = pgl.tesselate(geo_pgl.geometry)
    else:
        triset = pgl.tesselate(geo_pgl)
    
    ugrid = vtk.vtkUnstructuredGrid()
    ugrid_wrapped = dsa.UnstructuredGrid(ugrid)

    #extract points
    points = _pgl_pointarray_to_np(triset.pointList)
    
    #extract normals
    normal = _pgl_pointarray_to_np(triset.normalList)
    normal_vtk = nps.numpy_to_vtk(normal)

    #extract cells
    cells = _pgl_pointarray_to_np(triset.indexList, dtype=np.int32)
    triangle = vtk.vtkTriangle()
    CellArray = vtk.vtkCellArray()
    for c in cells:
        CellArray.InsertNextCell(3, c)
    if CellArray.CanConvertTo32BitStorage():
        CellArray.ConvertTo32BitStorage()

    #extract texCoord
    tex = _pgl_pointarray_to_np(triset.texCoordList)
    tex_vtk = nps.numpy_to_vtk(tex)

    ugrid_wrapped.Points = points
    ugrid_wrapped.GetPointData().SetNormals(normal_vtk)
    ugrid_wrapped.GetPointData().SetTCoords(tex_vtk)
    ugrid.SetCells(triangle.GetCellType(), CellArray)
    
    return ugrid

def huge_unstructured_grid(g, mtg_iterator = None):
    """
    Construct a huge unstructured grid that encodes the geo/topo of the mtg.
    The geometry is represented by a big unstructured grid obtained by concatenating all the grids of each mtg element.

    TODO : rewrite the function with append data set class

    The topology is given by the points data of the unstructured grid : for each point of the huge grid, there is given an attribute that indicates the id of the mtg node containing this point.
    The parent and the complex are also given under the data attribute in order to perfectly specify the topology.
    """
    if mtg_iterator is None:
        mtg_iterator = traversal.iter_mtg2(g,g.root)

    max_scale = g.max_scale()

    grid = vtk.vtkUnstructuredGrid()
    points = vtk.vtkPoints()
    cell = vtk.vtkTriangle()
    cell_type = cell.GetCellType()

    p_offset = 0 # points coordinates offset
    c_offset = 0 # cells connectivity offset

    mtg_id = vtk.vtkUnsignedIntArray()
    mtg_id.SetName("vid")
    
    parent_id = vtk.vtkIntArray()
    parent_id.SetName("parent_id")

    edge_type = vtk.vtkUnsignedIntArray()
    edge_type.SetName("edge_type")

    complex_id = vtk.vtkUnsignedIntArray()
    complex_id.SetName("complex_id")
    complex_id.SetNumberOfComponents(max_scale)

    label = vtk.vtkUnsignedIntArray()
    label.SetName("label")
    label_dict = {}
    
    # order = vtk.vtkUnsignedIntArray()
    # order.SetName("order")

    for vid in mtg_iterator:
        try:
            label_pt = label_dict[g.label(vid)]
        except KeyError:
            label_dict[g.label(vid)] = len(label_dict)
            label_pt = label_dict[g.label(vid)]

        geo = getattr(g.node(vid), "geometry")
        if geo is None:
            continue

        tri_mesh = pgl.tesselate(geo.geometry) # get the tri mesh
        
        parent = -1 if g.parent(vid) is None else g.parent(vid)
        edge_type_pt = 1 if g.edge_type(vid) == "+" else 0
        complex_id_pt = []
        complex = vid

        while complex is not None:
            complex = g.complex(complex)
            if complex is None:
                pass
            else:
                complex_id_pt.append(complex)

        # print(g.root, vid)
        # order_pt = g.AlgHeight(g.component_roots_at_scale(g.root,max_scale)[0], vid)
        
        # print(complex_id_pt)
        for pt in tri_mesh.pointList: # add all the points
            points.InsertNextPoint(*pt)
            
            mtg_id.InsertNextValue(vid)
            parent_id.InsertNextValue(parent)
            edge_type.InsertNextValue(edge_type_pt)
            label.InsertNextValue(label_pt)
            # order.InsertNextValue(order_pt)
            for c in complex_id_pt:
                complex_id.InsertNextValue(c)
   
        for cl in tri_mesh.indexList: # add all the cells
            for i,id in enumerate(cl): # for convert to vtk cell object
                cell.GetPointIds().SetId(i, id+p_offset) # add the cell offset
            grid.InsertNextCell(cell_type, cell.GetPointIds()) #insert into grid


        c_offset += len(tri_mesh.indexList)
        p_offset += len(tri_mesh.pointList)
    
    grid.SetPoints(points)

    grid.GetFieldData().AddArray(mtg_id)
    grid.GetFieldData().AddArray(parent_id)
    grid.GetFieldData().AddArray(edge_type)
    complex_id.SetNumberOfTuples(p_offset)
    grid.GetFieldData().AddArray(complex_id)
    grid.GetFieldData().AddArray(label)

    grid.GetFieldData().SetActiveScalars("vid")

    # print(p_offset)
    # print(complex_id.GetElementComponentSize())
    # grid.GetFieldData().AddArray(order)

    return grid,label_dict

def polydata(g, **kwargs):
    """
    This function convert the topology of mtg into a polydata object.
    See the specification of the corresponding polydata object in readme

    features are a dictionary that associates the feature to be written with there type

    VERY IMPORTANT : The method g.reindex() is called, we may lose the correspondance before/after writing the polydata
    """
    g.reindex()
    points_np = np.empty((len(g),3),dtype=np.float32)
    label_np = np.empty(len(g), dtype=np.uint8) # define an empty numpy array that we will add to polydata by wrapped vtk object.
    # It's important since the order of points and label are important.
    
    cells = vtk.vtkCellArray()
    EdgeType = vtk.vtkCharArray()
    EdgeType.SetName("EdgeType")
    
    label_dict = {}
    iterator_g = traversal.iter_mtg2(g,g.root)

    scalar_features = kwargs.get("scalar_features",None)
    vector_features = kwargs.get("vector_features",None)
    shapes = kwargs.get("shapes", None)
    has_geometry = kwargs.get("has_geometry", False)

    scalar_features_dict = _create_scalar_features(g, scalar_features)
    vector_features_dict = _create_vector_features(g, vector_features, shapes)
    
    if has_geometry:
        from opf_io.utils import mat_from_transformed
        geometry_features_dict = {"matrix":np.empty((len(g),9), dtype=np.float32), "translation":np.empty((len(g), 3), dtype=np.float32)}

    for vid in iterator_g:
        parent_id = g.parent(vid) # get the parent
        complex_id = g.complex(vid) # get the complex
        scale = g.scale(vid) # get the scale of the current node
        order = g.order(vid) # get the order of the current node
        points_np[vid,:] = [vid,order,scale] # insert one point, so this can create a geometry "by default" of the mtg
        
        # write the label
        label_no_numeric = re.sub(r"[0-9]+","",g.label(vid))
        try:
            label_code = label_dict[label_no_numeric]
        except KeyError:
            label_dict[label_no_numeric] = len(label_dict)
            label_code = label_dict[label_no_numeric]
        label_np[vid] = label_code
        # TODO write other attributes
        # to define numpy arrays and then we should use GetFieldData().append()
        for key in scalar_features_dict:
            attribute_value = getattr(g.node(vid), key)
            try:
                scalar_features_dict[key][vid] = attribute_value
            except TypeError:
                attribute_value = np.iinfo(str(scalar_features_dict[key].dtype)).max
                scalar_features_dict[key][vid] = attribute_value

        for key in vector_features_dict:
            attribute_value = getattr(g.node(vid), key)
            vector_features_dict[key][vid] = attribute_value

        if has_geometry:
            geo = getattr(g.node(vid), "geometry", None)
            if geo is None:
                mat = getattr(g.node(vid), "matrix", None)
                translation = getattr(g.node(vid), "translation", None)

                if mat is None:
                    geometry_features_dict["matrix"][vid,:] = np.array([float('nan')for i in range(9)])
                else:
                    # print("from mat : ", mat)
                    geometry_features_dict["matrix"][vid,:] = mat.flatten()

                if translation is None:   
                    geometry_features_dict["translation"][vid,:] = np.array([float('nan') for i in range(3)])
                else:
                    geometry_features_dict["translation"][vid,:] = translation.flatten()
            else:
                A = mat_from_transformed(geo)
                A_np = np.array([[A[(i,j)] for j in range(4)] for i in range(3)])
                # print("from geo : ", A_np)
                geometry_features_dict["matrix"][vid,:] = A_np[:3,:3].flatten()
                geometry_features_dict["translation"][vid,:] = A_np[:,3].flatten()

        # solve the topology
        if parent_id is not None:
            #if it's not a root node
            if complex_id != g.complex(parent_id): # if vid and it's parent are not in the same complex
                cells.InsertNextCell(2,(parent_id,complex_id))
                EdgeType.InsertNextValue(g.edge_type(vid))
                cells.InsertNextCell(2,(complex_id,vid))
                EdgeType.InsertNextValue("/")
                
            else: # if vid and it's parent are in the same complex
                cells.InsertNextCell(2,(parent_id,vid))
                EdgeType.InsertNextValue(g.edge_type(vid)) 
        else:
            if complex_id is not None:
                cells.InsertNextCell(2,(complex_id,vid))
                EdgeType.InsertNextValue("/")
    
    poly = vtk.vtkPolyData()

    poly_wrapped = dsa.PolyData(poly) #wrapped vtk object vtk.numpy_interface.dataset_adapter
    poly_wrapped.SetPoints(points_np) #it makes it easier to add information into a dataset
    poly_wrapped.GetFieldData().append(label_np, "label")
    
    label_meta_data = vtk.vtkStringArray()
    label_meta_data.SetName("label_names")
    label_meta_data.InsertNextValue(_label_meta_data(label_dict))
    poly_wrapped.VTKObject.GetFieldData().AddArray(label_meta_data)

    for key,value in scalar_features_dict.items():
        try:
            poly_wrapped.GetFieldData().append(value, key)
        except TypeError:
            if value.dtype == "object":
                pass
    for key, value in vector_features_dict.items():
        poly_wrapped.GetFieldData().append(value, key)
    if has_geometry:
        for key, value in geometry_features_dict.items():
            poly_wrapped.GetFieldData().append(value, key)

    # ues GetFieldData to add node attribut

    if cells.CanConvertTo32BitStorage():
        cells.ConvertTo32BitStorage()

    poly_wrapped.VTKObject.SetLines(cells)
    poly_wrapped.VTKObject.GetCellData().AddArray(EdgeType)
    
    

    return poly_wrapped.VTKObject, label_dict

def write(filename, data_set, label_dict=None, binary = True, XML = True):
    """
    Export the data set into the given file name
    The extension is managed automatically
    binary and xml control the output format
    """

    if isinstance(label_dict, dict):
        header = ",".join(["%s:%s"%(value,key) for key,value in label_dict.items()])

    if data_set.IsA("vtkUnstructuredGrid"):
        if XML:
            writer = vtk.vtkXMLUnstructuredGridWriter()
            ext = ".vtu"
        else:
            writer = vtk.vtkUnstructuredGridWriter()
            ext = ".vtk"
    elif data_set.IsA("vtkPolyData"):
        if XML:
            writer = vtk.vtkXMLPolyDataWriter()
            ext = ".vtp"
        else:
            writer = vtk.vtkPolyDataWriter()
            ext = ".vtk"
    else:
        raise(TypeError)
    vtk_name = "%s%s"%(filename,ext)
    writer.SetInputData(data_set)
    writer.SetFileName(vtk_name)
    writer.SetInputData(data_set)

    try :
        writer.SetHeader(header)
    except UnboundLocalError:
        pass
    except AttributeError:
        pass

    if not XML:
        if binary:
            writer.SetFileTypeToBinary()
    writer.Update()
    writer.Write()
    return vtk_name

def _create_scalar_features(g, scalar_features = None):
    """
    Create a dictionary for scalar features of g.
    Each key of the dictionary is associated to an empty numpy array that will be filled during the iteration of g.
    The lenght of the empty arrays are equal to the number of nodes in g.
    """
    fdict = {}
    if scalar_features is None:
        pass
    else:
        n = len(g)
        for name, feature_type in scalar_features.items():
            if not name in g.property_names():
                warn("The input mtg doesnot have the feature %s !" %(name))
            else:
                fdict[name] = np.empty(n, dtype=feature_type)
    return fdict

def _create_vector_features(g, vector_features = None, shapes = None):
    """
    Create a dictionary for vector features of g.
    Each key of the dictionary is associated to an empty numpy array that will be filled during the iteration of g.
    The shape of the empty arrays  = (len(g), number of components of the given featuer).

    Input : 
    vector_features : a dict {feature_name : type}
    shapes : a dict {feature_name : number of components}

    the two dict are supposed to have matching keys
    """
    fdict = {}

    if vector_features is None:
        pass
    else:
        n = len(g)
        for name, feature_type in vector_features.items():
            n_components = shapes[name]
            if not name in g.property_names():
                warn("The input mtg doesnot have feature %s !"%(name))
            else:
                fdict[name] = np.empty((n,n_components), dtype=feature_type)

    return fdict

def _label_meta_data(label_dict):
    """
    return a string that encode the mapping label and its code
    """
    gen = ("%s:%s"%(str(v),k) for k,v in label_dict.items())
    return ",".join(gen)

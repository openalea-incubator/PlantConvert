
import openalea.mtg.mtg as mtg
import openalea.plantgl.all as pgl
import vtkmodules.all as vtk
from vtkmodules.util import numpy_support as nps
from vtkmodules.numpy_interface import dataset_adapter as dsa
import numpy as np

def header_to_dict(header):
    """
    read the header as a dictionnary
    """
    return dict([tuple([int(h.split(":")[0]), h.split(":")[1]]) for h in header.split(",")])

def load_topology(filename):
    """
    Load into a vtk object from the file. It returns a tuple such that the second element is the header dictionary and the first element is the vtk object
    """
    if filename.endswith(".vtk"):
        # legacy format
        reader = vtk.vtkDataSetReader()
        reader.ReadAllFieldsOn() # use this command so that the reader will load all the fields data 
    elif filename.endswith(".vtp"):
        # xml format
        reader = vtk.vtkXMLPolyDataReader()
    else:
        raise ValueError("Unrecognized file extension")

    reader.SetFileName(filename)
    reader.Update()

    data_set = reader.GetOutput()
    
    if filename.endswith(".vtk"):
        header = reader.GetHeader()
    elif filename.endswith(".vtp"):
        header = data_set.GetFieldData().GetAbstractArray("label_names").GetValue(0)

    return data_set,header_to_dict(header)

def complex_vec(g,vid):
    """
    Get all the complexes of node vid from fine to coarsest scale
    """
    complex = []
    c = g.complex(vid)
    while c is not None:
        complex.append(c)
        c = g.complex(c)
    return complex

def mtg_from_huge_ugrid(filename):
    """
    This function build a mtg by reading in a file that encodes a huge unstructured grid (see function huge_unstructured_grid in write_vtk)

    TODO :
    the labels are lost in the mtg
    """
    ugrid = load_topology(filename)
    pt_data = ugrid.GetPointData()
    g = mtg.MTG()
    topology = {}
    i = 0
    while True: #extract information related to the topology
        name = pt_data.GetArrayName(i)
        if name is None:
            break
        else:
            if name in ["vid","parent_id","complex_id","edge_type","label"]:
                topology[name] = nps.vtk_to_numpy(pt_data.GetArray(i))
        i+=1
    print(topology.keys())
    # loop on the topology information
    # we only find the vid of finest scale, the decomposition is encoded in complex vector
    # if we repeat the same insert (g.add_component(i,j)) several times,
    # only the first time has effect
    last_added = -1
    for vid, parent_id, edge_type, complex,label in zip(*topology.values()): 
        if vid == last_added:
            continue

        if parent_id == -1:            # solve the decomposition using the complex vector
            complex_id = g.root
            for comp_id in complex[-2::-1]: # loop in reverse order from before last element 
                g.add_component(complex_id=complex_id, component_id=comp_id)
                complex_id = comp_id

            g.add_component(complex_id=complex_id, component_id=vid) # add 
            
        else:
            #solve edge type
            if edge_type == 1:
                edge = "+"
            else:
                edge = "<"
            # get the decomposition list of parent node
            complex_p = complex_vec(g, parent_id)

            for c_p, c_child in zip(complex_p[-2::-1],complex[-2::-1]):
                if c_p != c_child:
                    break #find the first different complex
            
            if c_p == c_child:
                #print(c_p,c_child)
                g.add_child(parent=parent_id, child=vid,edge_type=edge,label=str(label))

            else:
                #print(c_p,c_child)
                comp_p = parent_id
                comp_child = vid
                for complex_parent,complex_child in zip(complex_p,complex):
                    
                    if complex_parent == g.complex(c_p):
                        break
                    else:
                        g.add_child(parent=comp_p, child=comp_child,edge_type=edge)
                        g.add_child(parent=complex_parent, child=complex_child, edge_type=edge)
                        g.add_component(complex_id=complex_child, component_id=comp_child)

                    comp_p = complex_parent
                    comp_child = complex_child
                g.node(vid).label = str(label)
        last_added = vid
    return g


def mtg_from_polydata(filename):
    """
    This function constructs the mtg from a polydata file given by the filename. The header of the file should be interpreted as a dictionary giving correspondance between label and it's code.
    Parameter : 
    filename : relative path to the targer file
    
    TODO :
    Solve the attributes reading
    """
    
    polydata,label = load_topology(filename) #load the polydata object and get the header (that is transformed into dictionary)

    poly_wrap = dsa.WrapDataObject(polydata) #wrap the polydata for easier usaeg

    points = poly_wrap.Points #get the coordinates
    
    connectivity = nps.vtk_to_numpy(poly_wrap.VTKObject.GetLines().GetConnectivityArray()) #get the connectivity table

    label_poly = poly_wrap.FieldData['label'] #get the label of each mtg node
    edge_type = poly_wrap.GetCellData().GetArray("EdgeType") #get the edge type of each link

    #create a iterator to parse the topology information
    # the connectivity list is under the form : [parent child parent child ...].
    # by creating a iterator such that [0::2] [1::2] we can get iterate over parent and child id.
    topo_iter = zip(connectivity[0::2],connectivity[1::2],(chr(e) for e in edge_type)) 

    g = mtg.MTG()

    for parent_id,child_id,edge in topo_iter:
        #get the scale of the two nodes
        scale_p = points[parent_id][2]
        scale_c = points[child_id][2]
        label_child = label[label_poly[child_id]]
        if scale_p < scale_c: #if parent node is at lower scale
            g.add_component(complex_id=parent_id, component_id=child_id,label=label_child)
            #add attribute to child_id

        elif scale_p == scale_c:
            g.add_child(parent=parent_id,child=child_id,edge_type=edge, label=label_child)
            #add attribute to child_id

        else:# scale_p > scale_c: 
            complex_id, child_id, edge_new = next(topo_iter) #don't use edge_new as we know that'is necessarily /

            label_complex = label[label_poly[complex_id]]
            label_child = label[label_poly[child_id]]

            g.add_child_and_complex(parent=parent_id, child=child_id,complex=complex_id, edge_type=edge,label=label_child)
            g.node(complex_id).edge_type = edge
            g.node(complex_id).label = label_complex

            #add attribute to child_id

            #add attribute to complex_id

    for k in poly_wrap.FieldData.keys():
        if k != "label" and k!="label_names":
            try:
                FieldData_np = nps.vtk_to_numpy(poly_wrap.FieldData[k])
                dtype = str(FieldData_np.dtype)
            except ValueError:
                # i don't know why it's necessarily to transpose the matrix from reading. :'(
                FieldData_np = [np.array(mat).T for mat in poly_wrap.FieldData[k]]
                dtype = "float32"
            
            if dtype == "float32":
                g.properties()[k] = dict(((i,value) for i,value in enumerate(FieldData_np) if not np.any(np.isnan(value))))

            elif dtype == "int32":
                maxint = np.iinfo(dtype).max
                g.properties()[k] = dict(((i,value) for i,value in enumerate(FieldData_np) if not value == maxint))

    return g
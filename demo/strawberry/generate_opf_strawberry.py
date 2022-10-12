from os import path
import os

import openalea.strawberry as strawberry
from openalea.strawberry import import_mtgfile
from openalea.strawberry import visu3d

import openalea.mtg.mtg as mtg
from openalea.mtg.algo import orders

import openalea.plantgl.all as pgl

import format_io as f_io

DATA = "/".join(strawberry.__file__.split("/")[:-3])+"/share/data"
CAPRISS = DATA + "/Capriss.mtg"

def deep_print(geo, tab = 0):
    print("\t"*tab, end = "")
    print(geo)
    if hasattr(geo, "geometry"):
        deep_print(geo.geometry, tab = tab + 1)


def merge_shapes(shapes):
    
    if len(shapes) > 1:
        color = shapes[0].appearance
        geo = pgl.tesselate(pgl.Group(*[sh.geometry for sh in shapes]))
        if not isinstance(geo, pgl.TriangleSet):
            print(geo)
        return pgl.Shape(geo, color)
    else:
        # if there is only one shape in the list, we don't need to merge
        return shapes[0]

def deep_primitive(sh):
    if isinstance(sh, pgl.Shape):
        return deep_primitive(sh.geometry)
    elif isinstance(sh, pgl.Transformed):
        return deep_primitive(sh.geometry)
    else:
        return sh

def remove_bezier(scene_dict):
    keys = list(scene_dict.keys())
    shapes = list(scene_dict.values())
    poped_nb = 0
    for i,sh in enumerate(scene_dict.values()):
        if isinstance(deep_primitive(sh), pgl.BezierCurve2D):
            keys.pop(i-poped_nb)
            shapes.pop(i-poped_nb)
            poped_nb+=1
    return dict(zip(keys,shapes))

def main():

    gariguette = import_mtgfile.import_mtgfile(filename = ["Gariguette"])
    gariguette.properties()["order"] = orders(gariguette)
    # root = gariguette.root
    plants_id = gariguette.roots(scale = 1)
    # plant = gariguette.sub_mtg(plants_id[0], copy = True)

    scene = visu3d.plot3d(gariguette,by=["Sample_date"], hide_leaves = False, display = False)
    pgl.Viewer.display(scene)
    input()
    
    scene_dict = scene.todict()
    keys = iter(scene_dict.keys())
    merged = (merge_shapes(shapes) for shapes in scene_dict.values())
    scene_dict_merged = dict(zip(keys, merged))
    scene_dict_merged = remove_bezier(scene_dict_merged)
    
    f_io.opf.writer.apply_scene(gariguette, scene_dict_merged)

    io = f_io.io(ignored_name=["index","order","color"])
    io.g = gariguette
    io.write("gariguette.opf")

if __name__ == "__main__":
    main()
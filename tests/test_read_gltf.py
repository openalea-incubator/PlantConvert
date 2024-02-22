import numpy as np
import openalea.plantconvert as pc
import openalea.plantgl.all as pgl


def main():
    # you can try to other filename

    # fname="coffee"
    fname = "simple_plant"
    # fname = "DA1_Average_MAP_90"
    ext = "glb"
    io = pc.io(file="%s.%s" % (fname, ext))
    io.read()
    io.g.display()

    io.write("%s_test.gltf" % (fname))

    io2 = pc.io(file="%s_test.gltf" % (fname))
    io2.read()

    io.write("%s_test.opf" % (fname))

    scene1 = pc.geometry.get_scene(io.g)
    scene2 = pc.geometry.get_scene(io2.g)
    scene1.merge(scene2)
    error_ind = list(scene2.todict().keys())[73]
    np.array(io2.mtg_builder.gltf.nodes[error_ind].matrix).reshape((4, 4), order="F")
    pgl.Viewer.display(scene1)
    input()


if __name__ == "__main__":
    main()

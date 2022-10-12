import plantconvert as fio
from const import OPFS
import openalea.plantgl.all as pgl

def main():

    # fname="coffee"
    fname="simple_plant"
    # fname = "DA1_Average_MAP_90"
    ext = "opf"
    io = fio.io(file="%s%s.%s"%(OPFS, fname, ext))
    io.read()
    io.g.display()
    io.write("%s.gltf"%(fname))
    io.write("%s.glb"%(fname))

    ext = "gltf"
    io2 = fio.io(file="%s.%s"%(fname, ext))
    io2.read()
    io2.g.display()
    scene = fio.geometry.get_scene(io2.g)
    pgl.Viewer.display(scene)
    input()
    
if __name__ == "__main__":
    main()
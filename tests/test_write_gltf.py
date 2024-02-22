from openalea.plantconvert.plant import Plant
from openalea.plantconvert.geometry import get_scene
import openalea.plantgl.all as pgl


def main():
    directory = "data"
    fname = "simple_plant"
    ext = "opf"
    plant = Plant(file="%s%s.%s" % (directory, fname, ext))
    plant.read()
    plant.g.display()
    plant.write("%s.gltf" % (fname))
    plant.write("%s.glb" % (fname))

    ext = "gltf"
    plant2 = Plant(file="%s.%s" % (fname, ext))
    plant2.read()
    plant2.g.display()
    scene = get_scene(plant2.g)
    pgl.Viewer.display(scene)
    input()


if __name__ == "__main__":
    main()

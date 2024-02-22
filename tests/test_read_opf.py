#%%
import openalea.plantconvert as pc
import openalea.plantgl.all as pgl


#%%
def main():
    directory = "data"
    fname = "simple_plant"
    # fname = "DA1_Average_MAP_90"
    ext = "opf"
    plant = pc.plant.Plant(file="%s%s.%s" % (directory, fname, ext))
    plant.read()
    plant.mtg.display()
    print(plant.mtg[0]["user_attributes"])
    print(plant.mtg[0]["materials"])
    scene = pc.geometry.get_scene(plant.mtg)
    pgl.Viewer.display(scene)
    input()

#%%
if __name__ == "__main__":
    main()

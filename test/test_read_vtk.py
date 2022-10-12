import plantconvert as fio
from const import OPFS
import openalea.plantgl.all as pgl

def main():

    # fname="coffee"
    fname="simple_plant"
    # fname = "DA1_Average_MAP_90"
    io = fio.io(file="%s.vtp"%(fname))
    io.read()
    io.g.display()
    print(io.g.property_names())

if __name__ == "__main__":
    main()
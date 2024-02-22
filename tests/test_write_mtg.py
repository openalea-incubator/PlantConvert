import openalea.plantconvert as pc


def main():
    directory = "data"
    fname = "simple_plant"
    # fname = "DA1_Average_MAP_90"
    ext = "opf"
    io = pc.io(file="%s%s.%s" % (directory, fname, ext))
    io.read()
    # io.g.display()
    # print(io.g.property_names())
    io.write("%s.mtg" % (fname))


if __name__ == "__main__":
    main()

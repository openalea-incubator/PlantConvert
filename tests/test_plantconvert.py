import os

from openalea.mtg.mtg import MTG
from openalea.plantconvert.plant import Plant
from openalea.plantconvert.util import RESERVED_NAMES

directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data")


def test_read_opf():
    fname = "simple_plant"
    ext = "opf"
    plant = Plant(file="%s/%s.%s" % (directory, fname, ext))
    plant.read()

    assert isinstance(plant, Plant)
    assert isinstance(plant.mtg, MTG)
    assert plant.file == "%s/%s.%s" % (directory, fname, ext)
    assert plant.mtg.nb_vertices() == 7
    assert plant.mtg.nb_scales() == 4
    root = plant.mtg.root
    assert plant.mtg.nb_components(root) == 1
    opf_properties = RESERVED_NAMES + ["FileName", "Length", "Width", "XEuler"]
    opf_properties.remove("component_roots")
    assert set(plant.mtg.property_names()) == set(opf_properties)
    assert plant.mtg.property("Length") == {4: 0.1, 5: 0.2, 6: 0.1, 7: 0.2}
    assert plant.mtg.property("Width") == {4: 0.02, 5: 0.1, 6: 0.02, 7: 0.1}
    assert plant.mtg.property("materials")[0][0].shininess == 0.078125

def test_read_mtg():
    fname = "A3B4"
    ext = "mtg"
    plant = Plant(file="%s/%s.%s" % (directory, fname, ext))
    plant.read()
    assert isinstance(plant, Plant)
    assert isinstance(plant.mtg, MTG)
    assert plant.file == "%s/%s.%s" % (directory, fname, ext)
    assert plant.mtg.nb_vertices() == 612
    assert plant.mtg.nb_scales() == 3
    root = plant.mtg.root
    assert plant.mtg.nb_components(root) == 1
    assert plant.mtg.properties().keys() == {"edge_type", "label", "index",
                                             "XX", "YY", "ZZ", "radius",
                                             "_line"}
    assert plant.mtg.property("radius")[25] == 0.01451191222701318


def test_write_opf():
    fname = "A3B4"
    ext = "mtg"
    plant = Plant(file="%s/%s.%s" % (directory, fname, ext))
    plant.read()
    plant.write("%s/%s.opf" % (directory, fname))
    plant2 = Plant(file="%s/%s.opf" % (directory, fname))
    plant2.read()
    os.remove("%s/%s.opf" % (directory, fname))

    assert isinstance(plant2, Plant)
    assert isinstance(plant2.mtg, MTG)
    assert plant.mtg.property("edge_type") == plant2.mtg.property("edge_type")
    assert plant.mtg.property("radius") == plant2.mtg.property("radius")


def test_write_mtg():
    fname = "simple_plant"
    ext = "opf"
    plant = Plant(file="%s/%s.%s" % (directory, fname, ext))
    plant.read()
    plant.write("%s/%s.mtg" % (directory, fname))
    plant2 = Plant(file="%s/%s.mtg" % (directory, fname))
    plant2.read()
    os.remove("%s/%s.mtg" % (directory, fname))

    assert isinstance(plant2, Plant)
    assert isinstance(plant2.mtg, MTG)
    assert list(plant.mtg.property("edge_type").values()) == list(plant2.mtg.property("edge_type").values())
    assert list(plant.mtg.property("Length").values()) == list(plant2.mtg.property("Length").values())

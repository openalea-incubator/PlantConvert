.. _plantconvert_quick_start:

Quick start to use Plantconvert
###############################

You can load a plant object from one format into OpenAlea, visualize it, and convert it into another format:

.. code-block:: python

    import os
    from openalea.plantconvert.plant import Plant
    from openalea.plantconvert.geometry import get_scene
    import openalea.plantgl.all as pgl

    ext = "opf"
    simple_plant = "%s%s.%s" % ("../data/", "simple_plant", ext)
    plant = Plant(file=simple_plant)
    plant.read()

    scene = get_scene(plant.mtg)
    pgl.Viewer.display(scene)

    plant.write("simple_plant.gltf")

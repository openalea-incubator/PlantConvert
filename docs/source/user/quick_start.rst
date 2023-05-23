.. _plantconvert_quick_start:

Quick start to use Plantconvert
###############################

You can load a plant object from one format into OpenAlea, visualize it, and convert it into another format:

.. code-block:: python

  import os
  from plantconvert.plantconvert import Plant 
  import openalea.plantgl.all as pgl

  ext = "opf"
  simple_plant = "%s%s.%s"%("../data/", "simple_plant", ext)
  plant = Plant(file=simple_plant)
  plant.read()
  
  scene = pc.geometry.get_scene(plant.mtg)
  pgl.Viewer.display(scene)

  plant.write("simple_plant.gltf")

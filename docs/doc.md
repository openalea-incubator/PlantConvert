- gltf, opf, vtk : submodules where the actual implementations of reader/ writer are found, direct usage of those submodules are not recommended. It's only recommand to use the function `opf.writer.apply_scene(g, scene)` to save a scene into input mtg `g` in a manner that satisfies the `opf` writer. The user should carefully construct the scene object such that `scene.todict()` returns a dictionary with mtg vertices as keys and with corresponding meshes as values


- geometry : use the method `get_scene(g)` to extract geoemtry attributes of an mtg and build a scene object from geometric elements.

There are also some useful functions in `binary_tools` and `matrix`.

The first one convert data array into a binary string that can be written into a file efficiently. The second one provides interface between plantgl matrices and numpy matrices and provides special cases of some matrix decomposition adapted to the context of 3D rendering (for example QR decomposition in the spectial context of translation-rotation-scaling matrix).


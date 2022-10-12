# MTG and its input/output into multiple formats

This project allows you to read and write mtg into mulitiple formats :
1. homemade .mtg and .opf file formats
2. gltf/glb
3. vtk/vtp

## Installation
You need first to install the conda environment `opf.yml`. After that you should install `pygltflib` and `vtk` by pip : 
```
pip install pygltflib
pip install vtk
```

If you would like to have example dataset of mtg with geometries, please install the conda envrionment `strawberry.yml` and please also install `pygltflib` and `vtk` by pip in the new environment.

For instance, there is not yet available setup tool for current package, please source the bash script `add.sh` one time before you launch Python scripts that require the package. This bash script 

## .mtg and .opf

They are encoded in ascii and directly parsed to construct a mtg object. 
`.mtg` is the default file format used by `openalea` and it only allows to save geometric parameters and not meshes.
The `.opf` is a historical file formats used by archimed plateform and allows to save both the topologic and geometric information.

## .gltf and .glb
They are `.json` styled file format designed to transmit computer graphics object by web. It allows to save topologic information by creating a scene graph (tree graph that explains the hierarchy of visible objects), we exploit this functionality to save the plants' topology in those file format. The attributes of an mtg are saved as `extras` field of each node of the scene graph.

We can insert references to meshes inside the `.gltf` file. `.glb` is the same as `.gltf` but with mesh data embedded inside the same file. 

We parse the `.gltf` file by using the `Python` package `pygltflib`. It constructs a `gltf` Python object that is converted to a mtg object.

## vtk/vtp
They are classic file formats with a large spectrum of geometric tools associated. We use this file formats to save the topology of a plants using polylines. A mtg node is viewed as a point with coordinates of the polylines, the branching system is viewed as segments of polylines, the edge type can be seen as an edge variable of polyline.

The attributes can be saved as points variables. 

These formats are very efficient in terms of memory usage, they allow to save data in binary format.

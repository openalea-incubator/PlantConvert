==================================
Developer Install - Ubuntu (linux)
==================================

.. contents::


1. Miniconda installation
-------------------------

Follow official website instruction to install miniconda :

https://docs.conda.io/en/latest/miniconda.html

2. Create virtual environment and activate it
---------------------------------------------

In Anaconda Prompt:

.. code:: shell

    conda create --name openalea -c conda-forge -c openalea3 openalea.plantgl openalea.mtg -y
    conda activate openalea


3. Install the plantconvert package
---------------------------------

.. code:: shell

    git clone https://github.com/openalea/plantconvert.git
    cd plantconvert
    python setup.py develop

4. Optional packages
---------------------

.. code:: shell

    conda install -c conda-forge pytest

.. highlight:: shell

Installation
------------


Stable release
==============

.. warning

        `OpenAlea.PlantConvert`` is not yet available on PyPI. This section will be updated when it is.
        Please use the "From sources" section for now.

To install OpenAlea.PlantConvert, run this command in your terminal:

.. code-block:: console

    $ pip install plantconvert

This is the preferred method to install OpenAlea.PlantConvert, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
============

The sources for OpenAlea.PlantConvert can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/openalea-incubator/plantconvert

Or download the `tarball`_:

.. code-block:: console

    $ curl -OJL https://github.com/openalea-incubator/plantconvert/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ pip install .


.. _Github repo: https://github.com/thomasasouze/plantconvert
.. _tarball: https://github.com/thomasasouze/plantconvert/tarball/master


Developer Install
=================

1. Miniconda installation
'''''''''''''''''''''''''

Follow official website instruction to install miniconda :

https://docs.conda.io/en/latest/miniconda.html

2. Create virtual environment and activate it
'''''''''''''''''''''''''''''''''''''''''''''

In Anaconda Prompt:

.. code:: shell

    conda create --name openalea -c conda-forge -c openalea3 openalea.plantgl openalea.mtg -y
    conda activate openalea


3. Install the plantconvert package
'''''''''''''''''''''''''''''''''''

.. code:: shell

    git clone https://github.com/openalea/plantconvert.git
    cd plantconvert
    pip install -e .

4. Optional packages
'''''''''''''''''''''

.. code:: shell

    conda install -c conda-forge pytest

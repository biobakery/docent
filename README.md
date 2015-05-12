This script performs the following steps:

  1. Installs a virtual environment (with `virtualenv`)
  2. Installs a list of python packages into the virtualenv
  3. Exposes a list of scripts by creating wrapper scripts 
     named as the scripts to be exposed.

This solves the problem of having two python scripts on the same
machine that need different versions of the same python package (I'm
looking at you, Numpy).

Options can either be set on the command line via flags or sent
wholesale to stdin in json format. Example json files are available in
the `specs` directory of wherever you downloaded the code prior to
running `setup.py install` 
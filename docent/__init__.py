import os
import sys
import json
import subprocess
import optparse
from functools import partial
from cStringIO import StringIO

from . import matcher

HELP=\
"""
        %prog [ options ] 

        %prog [ options ] < spec.json


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
"""

opts_list = [
    optparse.make_option(
        "-i", "--install", action="append",
        dest="pip_install_list", default=list(),
        help=("Specify a package to install. "
              "Understands whatever pip understands")),
    optparse.make_option(
        '-o', '--expose', action="append",
        dest="to_expose_list", default=list(),
        help="Expose this script from the virtualenv"),
    optparse.make_option(
        '-v', '--verbose', action="store_true",
        dest="verbose", default=False,
        help="Be verbose"),
    optparse.make_option(
        '-q', '--quiet', action="store_true",
        dest="quiet", default=False,
        help="Be quiet."),
    optparse.make_option(
        '-e', '--virtualenv_dir', action="store",
        dest="venv_dir", default=None,
        help="Specify where the virtualenv should live"),
    optparse.make_option(
        '-t', '--template', action="store",
        dest="template", default=None,
        help="Specify alternate wrapper shell script template"),
    optparse.make_option(
        '-a', '--virtualenv_args', action="store",
        dest="venv_args", default="",
        help="Specify extra arguments to to virtualenv"),
    optparse.make_option(
        '-j', '--jsonspec', action="store",
        dest="jsonspec", default=None,
        help="Interpret json-formatted spec file (overridden by cli flags)"),
]


default_venv_name = "docent_virtualenv"

_default_template = None
def default_template():
    global _default_template
    if not _default_template:
        here = os.path.abspath(os.path.dirname(__file__))
        with open(os.path.join(here, "script_template.txt")) as f:
            _default_template = f.read()
    return _default_template


def pop(dict_, items):
    for item in items:
        dict_.pop(item, None)

def init_sh(verbose=False):
    if verbose:
        return sh
    else:
        def new_sh(*args, **kwargs):
            pop(kwargs, ["stdout","stderr"])
            ret, (out, err) = sh(stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                                 *args, **kwargs)
            if ret:
                print >> sys.stderr, out
                print >> sys.stderr, err
                msg = "Process returned nonzero exit status of "
                raise OSError(msg+str(ret))
        return new_sh


def sh(args, **kwargs):
    kwargs.pop("shell", None)
    proc = subprocess.Popen(args, shell=True, **kwargs)
    out, err = proc.communicate()
    return proc.wait(), (out, err)


def handle_verbose(be_verbose):
    log = lambda msg, *args: sys.stderr.write(msg.format(*args))
    if be_verbose is None: # be quiet
        log = lambda msg, *args: None
        be_verbose = False
    return log, init_sh(be_verbose)


def expose(name, activate_script, template=None):
    if not template:
        template = default_template()

    with open(name, 'w') as f:
        print >> f, template %({"activate_script": activate_script,
                                "name": os.path.basename(name)})
    os.chmod(name, 0o755)


def install_venv(sh=sh, path=None, extra_args=""):
    if not path:
        path = default_venv_name
    sh("virtualenv {} {}".format(extra_args, path))
    return os.path.join(path, "bin", "activate")


def install(pip_install_list, to_expose_list, venv_dir=None,
            template=None, verbose=False, venv_args=""):
    if not to_expose_list:
        raise ValueError("List of scripts to expose can't be empty")

    log, sh = handle_verbose(verbose)

    if os.path.exists(os.path.join(venv_dir, "bin", "activate")):
        log("Virtualenv {} exists. Skipping virtualenv installation.\n",
            venv_dir)
    else:
        log("Installing virtualenv to {}...", venv_dir or default_venv_name)
        activate_script = install_venv(
            sh=sh, path=venv_dir, extra_args=venv_args)
        log("Done.\n")

    if any(pip_install_list):
        log("Installing requirements...")
        for req_str in pip_install_list:
            sh("source {}; pip install {}".format(activate_script, req_str))
        log("Done.\n")

    for to_expose in to_expose_list:
        log("Exposing script {}...", to_expose)
        expose(to_expose, activate_script, template)
        log("Done.\n")

    log("Complete.\n")


def error(msg, retcode=1):
    print >> sys.stderr, str(msg)
    return retcode


def main():
    opts, args = optparse.OptionParser(
        option_list=opts_list, usage=HELP
    ).parse_args()

    defaults = {'pip_install_list': opts.pip_install_list,
                'to_expose_list': opts.to_expose_list,
                'venv_dir': opts.venv_dir,
                'template': opts.template,
                'verbose': None if opts.quiet else opts.verbose,
                'venv_args': opts.venv_args}

    kwargs = {}
    if not sys.stdin.isatty():
        kwargs = json.load(sys.stdin)
    elif opts.jsonspec:
        with open(opts.jsonspec) as f:
            kwargs = json.load(f)

    for key, val in kwargs.iteritems():
        if key not in defaults:
            match = matcher.find_match(key, defaults.keys())
            msg = ("Unrecognized parameter in json spec `{}'. "
                   "Perhaps you meant `{}'")
            return error(msg.format(key, match))
        if not defaults[key]:
            defaults[key] = val

    try:
        install(**defaults)
    except ValueError as e:
        return error(e)
    

if __name__ == '__main__':
    ret = main()
    sys.exit(ret)

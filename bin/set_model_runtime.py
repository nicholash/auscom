#!/usr/bin/env python

import argparse
import sys
import re
from datetime import datetime, timedelta

"""
Modify atmosphere, ice, ocean and coupler namelists files to set experiment runtime.

It depends on the the experiments directory being at ../exp
"""

input_atm = "../exp/%s/ATM_RUNDIR/input_atm.nml"
namcouple = ["../exp/%s/ATM_RUNDIR/namcouple", "../exp/%s/OCN_RUNDIR/namcouple", "../exp/%s/ICE_RUNDIR/namcouple"]
input_ice = "../exp/%s/ICE_RUNDIR/input_ice.nml"
input_ocn = "../exp/%s/OCN_RUNDIR/input.nml"

class FortranNamelist:
    """
    Class to represent a Fortran namelist file.

    Can be used to modify fields.
    """

    def __init__(self, filename):
        self.filename = filename
        with open(filename, 'r') as f:
            self.str = f.read()

    def set_value(self, variable, value, record=None):
        regex = r"%s[ \t]*=[ \t]*(\S*),?[ \t]*$"
        if record is None:
            m = re.search(regex % (variable), self.str, re.MULTILINE | re.DOTALL)
        else:
            m = re.search((r"&%s.*?" + regex) % (record, variable), self.str, re.MULTILINE | re.DOTALL)
        assert(m is not None)

        self.str = self.str[:m.start(1)] + str(value) + self.str[m.end(1):]

    def write(self):
        with open(self.filename, 'w') as f:
            f.write(self.str)

class Namcouple:
    """
    Class to represent an OASIS namcouple file. 

    Allows fields to be modified.

    Presently only supports $RUNTIME
    """

    def __init__(self, filename):
        self.filename = filename
        with open(filename, 'r') as f:
            self.str = f.read()

    def set_runtime(self, runtime):

        m = re.search(r"^[ \t]*\$RUNTIME.*?^[ \t]*(\d+)", self.str, re.MULTILINE | re.DOTALL)
        assert(m is not None)
        self.str = self.str[:m.start(1)] + runtime + self.str[m.end(1):]

    def write(self):
        with open(self.filename, 'w') as f:
            f.write(self.str)

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", help="The experiment on which to change the runtime.")
    parser.add_argument("runtime", help="The runtime in seconds.")

    args = parser.parse_args()

    # Change runtime in the namcouple files.
    for n in namcouple:
        nc = Namcouple(n % (args.experiment))
        nc.set_runtime(args.runtime)
        nc.write()

    nml = FortranNamelist(input_atm % (args.experiment))
    nml.set_value('runtime', args.runtime)
    nml.write()

    nml = FortranNamelist(input_ice % (args.experiment))
    nml.set_value('runtime', args.runtime)
    nml.write()

    sec = timedelta(seconds=int(args.runtime))
    d = datetime(1, 1, 1) + sec

    nml = FortranNamelist(input_ocn % (args.experiment))
    nml.set_value('months', d.month - 1, record='ocean_solo_nml')
    nml.set_value('days', d.day - 1, record='ocean_solo_nml')
    nml.set_value('hours', d.hour, record='ocean_solo_nml')
    nml.set_value('minutes', d.minute, record='ocean_solo_nml')
    nml.set_value('seconds', d.second, record='ocean_solo_nml')
    nml.write()

if __name__ == "__main__":
    sys.exit(main())

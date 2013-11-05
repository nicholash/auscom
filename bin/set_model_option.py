#!/usr/bin/env python

import argparse
import sys
import re
from datetime import datetime, timedelta

"""
Modify atmosphere, ice, ocean and coupler namelists files to set a configuration option.

Relies on the the experiments directory being at ../exp
"""

input_atm = "../exp/%s/ATM_RUNDIR/input_atm.nml"
namcouple = ["../exp/%s/ATM_RUNDIR/namcouple", "../exp/%s/OCN_RUNDIR/namcouple", "../exp/%s/ICE_RUNDIR/namcouple"]
input_ice = "../exp/%s/ICE_RUNDIR/input_ice.nml"
cice_in = "../exp/%s/ICE_RUNDIR/cice_in.nml"
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

    def get_value(self, variable, record=None):
        """
        Return the value, start index and end index.
        """
        regex = r"%s[ \t]*=[ \t]*(\S*),?[ \t]*$"
        if record is None:
            m = re.search(regex % (variable), self.str, re.MULTILINE | re.DOTALL)
        else:
            m = re.search((r"&%s.*?" + regex) % (record, variable), self.str, re.MULTILINE | re.DOTALL)
        assert(m is not None)

        return (m.group(1), m.start(1), m.end(1))

    def set_value(self, variable, value, record=None):

        (_, start, end) = self.get_value_match(variable, record)

        self.str = self.str[:start] + str(value) + self.str[m.end(1):]

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

    def set_ocean_timestep(self, timestep):

        def substitute_timestep(regex):
            """
            Make one change at a time, each change affects subsequent matches.
            """
            while True:
                matches = re.finditer(regex, self.str, re.MULTILINE | re.DOTALL)
                none_updated = True
                for m in matches:
                    if m.group(1) == timestep:
                        continue
                    else:
                        self.str = self.str[:m.start(1)] + timestep + self.str[m.end(1):]
                        none_updated = False
                        break

                if none_updated:
                    break

        substitute_timestep(r"nt62 cice LAG=\+(\d+) ")
        substitute_timestep(r"cice nt62 LAG=\+(\d+) ")
        substitute_timestep(r"\d+ (\d+) \d+ i2o.nc EXPORTED")
        substitute_timestep(r"\d+ (\d+) \d+ o2i.nc EXPORTED")

    def write(self):
        with open(self.filename, 'w') as f:
            f.write(self.str)

def set_runtime(experiment, runtime):

    # Change runtime in the namcouple files.
    for n in namcouple:
        nc = Namcouple(n % (experiment))
        nc.set_runtime(runtime)
        nc.write()

    nml = FortranNamelist(input_atm % (experiment))
    nml.set_value('runtime', runtime)
    nml.write()

    nml = FortranNamelist(input_ice % (experiment))
    nml.set_value('runtime', runtime)
    nml.write()

    sec = timedelta(seconds=int(runtime))
    d = datetime(1, 1, 1) + sec

    nml = FortranNamelist(input_ocn % (experiment))
    nml.set_value('months', d.month - 1, record='ocean_solo_nml')
    nml.set_value('days', d.day - 1, record='ocean_solo_nml')
    nml.set_value('hours', d.hour, record='ocean_solo_nml')
    nml.set_value('minutes', d.minute, record='ocean_solo_nml')
    nml.set_value('seconds', d.second, record='ocean_solo_nml')
    nml.write()

def set_ocean_timestep(experiment, timestep):

    # Change runtime in the namcouple files.
    for n in namcouple:
        nc = Namcouple(n % (experiment))
        nc.set_ocean_timestep(timestep)
        nc.write()

    nml = FortranNamelist(input_atm % (experiment))
    nml.set_value('dt_atm', timestep)
    nml.write()

    nml = FortranNamelist(input_ice % (experiment))
    nml.set_value('dt_cpl_io', timestep)
    nml.set_value('dt_cice', timestep)
    nml.write()

    nml = FortranNamelist(cice_in % (experiment))

    # Read in the current timestep and runtime, needed to calculate new runtime (in units of timestep). 
    (dt, _, _) = nml.get_value('dt')
    (npt, _, _) =  nml.get_value('npt')
    runtime = dt*npt
    new_npt = runtime // timestep

    nml.set_value('dt', timestep)
    nml.set_value('npt', new_npt)
    nml.write()

    nml = FortranNamelist(input_ocn % (experiment))
    nml.set_value('dt_ocean', timestep)
    nml.set_value('dt_cpl', timestep)
    nml.set_value('dt_cpld', timestep)
    nml.write()

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", help="The experiment on which to change the runtime.")
    parser.add_argument("--runtime", dest="runtime", help="The runtime in seconds.")
    parser.add_argument("--ocean_timestep", dest="ocean_timestep", help="The ocean timestep in seconds.")

    args = parser.parse_args()

    if args.runtime:
        set_runtime(args.experiment, args.runtime)
    if args.ocean_timestep:
        set_ocean_timestep(args.experiment, args.ocean_timestep)

if __name__ == "__main__":
    sys.exit(main())

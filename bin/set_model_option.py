#!/usr/bin/env python

import argparse
import sys
import re
from fnamelist import FortranNamelist, Namcouple
from datetime import datetime, timedelta

"""
Modify atmosphere, ice, ocean and coupler namelists files to set a configuration option.

Relies on the the experiments directory being at ../exp
"""

input_atm = "../exp/%s/input_atm.nml"
namcouple = ["../exp/%s/namcouple"]
input_ice = "../exp/%s/input_ice.nml"
cice_in = "../exp/%s/cice_in.nml"
input_ocn = "../exp/%s/input.nml"


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
    nml.set_value('years', d.year - 1, record='ocean_solo_nml')
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

    nml = FortranNamelist(input_ocn % (experiment))
    nml.set_value('dt_ocean', timestep)
    nml.set_value('dt_cpl', timestep)
    nml.set_value('dt_cpld', timestep)
    nml.write()

    nml = FortranNamelist(input_ice % (experiment))
    nml.set_value('dt_cpl_io', timestep)
    nml.write()

def set_ice_timestep(experiment, timestep):

    nml = FortranNamelist(input_ice % (experiment))
    nml.set_value('dt_cice', timestep)
    nml.write()

    nml = FortranNamelist(cice_in % (experiment))

    # Read in the current timestep and runtime, needed to calculate new runtime (in units of timestep). 
    (dt, _, _) = nml.get_value('dt')
    (npt, _, _) =  nml.get_value('npt')
    runtime = int(dt)*int(npt)
    new_npt = runtime // int(timestep)

    nml.set_value('dt', timestep)
    nml.set_value('npt', new_npt)
    nml.write()

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", help="The experiment on which to change the runtime.")
    parser.add_argument("--runtime", dest="runtime", help="The runtime in seconds.")
    parser.add_argument("--ocean_timestep", dest="ocean_timestep", help="The ocean timestep in seconds.")
    parser.add_argument("--ice_timestep", dest="ice_timestep", help="The ice timestep in seconds.")

    args = parser.parse_args()

    if args.runtime:
        set_runtime(args.experiment, args.runtime)
    if args.ocean_timestep:
        set_ocean_timestep(args.experiment, args.ocean_timestep)
    if args.ice_timestep:
        set_ice_timestep(args.experiment, args.ice_timestep)

if __name__ == "__main__":
    sys.exit(main())

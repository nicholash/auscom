#!/usr/bin/env python

"""
Remove the time dimension from a field.
"""

import sys
import shutil
import netCDF4 as nc
import numpy as np

def main():

    # Copy some bits.
    cmd = \
    """
    ncks -v GRID_X_T monthly_sstsss.ext.nc monthly_sstsss.ext.no_time.nc &&
    echo "a" | ncks -v GRID_Y_T monthly_sstsss.ext.nc monthly_sstsss.ext.no_time.nc
    """
    os.system(cmd)

    f_orig = nc.Dataset('monthly_sstsss.ext.nc', 'r')
    f_new = nc.Dataset('monthly_sstsss.ext.no_time.nc', 'r+')

    salt_new = f_new.createVariable('SALT', 'f8', ('GRID_Y_T', 'GRID_X_T'))
    temp_new = f_new.createVariable('TEMP', 'f8', ('GRID_Y_T', 'GRID_X_T'))

    salt_new[:,:] = f_orig.variables['SALT'][0,:,:]
    temp_new[:,:] = f_orig.variables['TEMP'][0,:,:]

if __name__ == "__main__":
    sys.exit(main())

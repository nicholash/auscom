#!/usr/bin/env python

"""
Extend the CICE grid and data further South.

This is done by just extending the latitudes of the southern most grid points. 
"""

import sys
import shutil
import netCDF4 as nc
import numpy as np

r_Earth = 6.371009e6

def main():

    # Make a copy of the files that will be changed.
    shutil.copy('grid.nc', 'grid.ext.nc')
    shutil.copy('u_star.nc', 'u_star.ext.nc')
    shutil.copy('monthly_sstsss.nc', 'monthly_sstsss.ext.nc')

    # Read in the grid and field files. 
    grid = nc.Dataset('grid.ext.nc', 'r+')
    u_star = nc.Dataset('u_star.ext.nc', 'r+')
    temp_salt = nc.Dataset('monthly_sstsss.ext.nc', 'r+')

    # Extend Southern u points
    ulat = grid.variables['ulat']
    ulon = grid.variables['ulon']
    ulat_tmp = ulat[0, 0]
    ulat[0, :] = -1.41413909065909
    ulat_diff = ulat[0, 0] - ulat_tmp

    # Extent Southern t points
    tlat = grid.variables['tlat']
    tlon = grid.variables['tlon']
    tlat_tmp = tlat[0, 0]
    tlat[0, :] = -1.41506061219264
    tlat_diff = tlat[0, 0] - tlat_tmp

    # Fix up width of cells on E side, N is unchanged. Units are cm.
    grid.variables['hte'][0, :] = (tlat[1, :] - tlat[0, :]) * r_Earth * 100
    grid.variables['hue'][0, :] = (ulat[1, :] - ulat[0, :]) * r_Earth * 100

    # Fix up uarea and tarea.
    grid.variables['tarea'][0, :] = (tlon[1, 1] - tlon[1, 0]) * (np.sin(tlat[1, 0]) - np.sin(tlat[0, 0])) * r_Earth**2
    grid.variables['uarea'][0, :] = (ulon[1, 1] - ulon[1, 0]) * (np.sin(ulat[1, 0]) - np.sin(ulat[0, 0])) * r_Earth**2

    # Fix up latitudes of T and U cell vertices. Just add the same diff from the points.
    latu_bonds = grid.variables['latu_bonds']
    latu_bonds[0,0,:] = latu_bonds[0, 0, :] + ulat_diff
    latu_bonds[2,0,:] = latu_bonds[2, 0, :] + ulat_diff
    latt_bonds = grid.variables['latt_bonds']
    latt_bonds[0,0,:] = latt_bonds[0, 0, :] + tlat_diff
    latt_bonds[2,0,:] = latt_bonds[2, 0, :] + tlat_diff

    # Change the min u_start latitude. 
    u_star.variables['GRID_Y_T'][0] = np.rad2deg(-1.41506061219264)
    temp_salt.variables['GRID_Y_T'][0] = np.rad2deg(-1.41506061219264)

    grid.close()
    u_star.close()
    temp_salt.close()

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python

import sys
import os
import argparse
import numpy as np
import subprocess

import netCDF4 as nc

"""
Create OASIS masks, areas and grids files based on MOM5 grid.
The created files are written in the current directory.
"""

def make_masks(ocean_mask, oasis_mask):
    """
    Read in mom5-0.25 mask, invert and write out in the format that OASIS expects.
    """

    # Copy over mask from ocean. 
    cmd = \
"""
ncks -v nt62.msk %s masks.nc &&
echo "a" | ncks -v mask %s masks.nc &&
echo "y" | ncrename -v mask,cice.msk masks.nc masks.nc
""" % (oasis_mask, ocean_mask)
    os.system(cmd)

    # Invert the mask for OASIS.
    f = nc.Dataset('masks.nc', 'r+')

    tmp = f.variables['cice.msk'][:]
    tmp = tmp.astype(bool)
    tmp = ~tmp
    tmp = tmp.astype(int)

    f.variables['cice.msk'][:] = tmp[:]
    # Fix up units.
    f.variables['cice.msk'].units = f.variables['nt62.msk'].units

    f.close()

def make_areas(ocean_grid, oasis_area):
    """
    Copy nt62 surface areas from oasis areas. Copy ocean surface areas. 
    """

    cmd = """\
ncks -v nt62.srf %s areas.nc &&
echo "a" | ncks -v tarea %s areas.nc &&
echo "y" | ncrename -v tarea,cice.srf areas.nc areas.nc""" % (oasis_area, ocean_grid)

    os.system(cmd)

def split_double_density_test(x, y):
    """
    Split a double density grid into t cell points and corners.

    Only needed for testing.
    """

    # Latitude of corners.
    cla = np.empty((4, x.shape[0] / 2, x.shape[1] / 2))
    cla[:] = np.NAN
    # Longitude of corners.
    clo = np.empty(cla.shape)
    clo[:] = np.NAN

    # t-cell lats and lons 
    lat = np.empty((x.shape[0] / 2, x.shape[1] / 2))
    lat[:] = np.NAN
    lon = np.empty(lat.shape)
    lon[:] = np.NAN

    for it in range(clo.shape[2]):
        for jt in range(clo.shape[1]):
            
            i = it*2 + 1
            j = jt*2 + 1

            cla[0, jt, it] = y[j - 1, i - 1] 
            cla[1, jt, it] = y[j - 1, i + 1]
            cla[2, jt, it] = y[j + 1, i + 1]
            cla[3, jt, it] = y[j + 1, i - 1]

            clo[0, jt, it] = x[j - 1, i - 1] 
            clo[1, jt, it] = x[j - 1, i + 1]
            clo[2, jt, it] = x[j + 1, i + 1]
            clo[3, jt, it] = x[j + 1, i - 1]

            lat[jt, it] = y[j, i]
            lon[jt, it] = x[j, i]


    return (lat, lon, cla, clo)

def make_grids(ocean_grid, oasis_grid):
    """
    Gather together all the fields needed for the grids.nc file.
    """

    cmd = \
"""
ncks -v nt62.lon %s grids.nc &&
echo "a" | ncks -v nt62.lat %s grids.nc &&
echo "a" | ncks -v nt62.cla %s grids.nc &&
echo "a" | ncks -v nt62.clo %s grids.nc 
""" % (oasis_grid, oasis_grid, oasis_grid, oasis_grid)
    os.system(cmd)

    # Split up the double density grid into t anc c points.
    f = nc.Dataset(ocean_grid, 'r')

    # Copy netcdf variables, otherwise access is very slow.
    x = np.copy(f.variables['x'])
    y = np.copy(f.variables['y'])
    f.close()

    lat = np.empty((x.shape[0] / 2, x.shape[1] / 2))
    lon = np.empty(lat.shape)
    cla = np.empty((4, lat.shape[0], lat.shape[1]))
    clo = np.empty(cla.shape)

    # T cell lat, lons.
    lat[:] = y[1::2,1::2]
    lon[:] = x[1::2,1::2]

    # Corner lats.
    cla[0,:,:] = y[0:-1:2,0:-1:2]
    cla[1,:,:] = y[0:-1:2,2::2]
    cla[2,:,:] = y[2::2,2::2]
    cla[3,:,:] = y[2::2,0:-1:2]

    # Corner lons.
    clo[0,:,:] = x[0:-1:2,0:-1:2]
    clo[1,:,:] = x[0:-1:2,2::2]
    clo[2,:,:] = x[2::2,2::2]
    clo[3,:,:] = x[2::2,0:-1:2]

    # Take a different appoach to the above and compare as a test.
    (lat_t, lon_t, cla_t, clo_t) = split_double_density_test(x, y)
    np.testing.assert_array_equal(lat_t, lat)
    np.testing.assert_array_equal(lon_t, lon)
    np.testing.assert_array_equal(clo_t, clo)
    np.testing.assert_array_equal(cla_t, cla)

    f = nc.Dataset('grids.nc', 'r+')

    f.createDimension('nyo', lat.shape[0])
    f.createDimension('nxo', lat.shape[1])
    f.createDimension('nco', 4)
    cice_lat = f.createVariable('cice.lat', 'f8', ('nyo', 'nxo'))
    cice_lat.units = "degrees_north"
    cice_lat.title = "geographic_latitude"

    cice_lon = f.createVariable('cice.lon', 'f8', ('nyo', 'nxo'))
    cice_lon.units = "degrees_east"
    cice_lon.title = "geographic_longitude"

    cice_cla = f.createVariable('cice.cla', 'f8', ('nco', 'nyo', 'nxo'))
    cice_cla.units = "degrees_north"
    cice_cla.title = "cice grid T-cell corner latitude"

    cice_clo = f.createVariable('cice.clo', 'f8', ('nco', 'nyo', 'nxo'))
    cice_clo.units = "degrees_east"
    cice_clo.title = "cice grid T-cell corner longitude"

    cice_lat[:] = lat[:]
    cice_lon[:] = lon[:]
    cice_cla[:] = cla[:]
    cice_clo[:] = clo[:]

    f.close()

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("ocean_grid", help="Input MOM5 grid, needed to create new OASIS files.")
    parser.add_argument("ocean_mask", help="Input MOM5 mask, needed to create new OASIS files.")
    parser.add_argument("masks", help="Existing OASIS masks file, this should not be in the current directory. \
                                       The newly created masks file is written to the current directory.")
    parser.add_argument("grids", help="Existing OASIS grids file.")
    parser.add_argument("areas", help="Existing OASIS areas file.")

    args = parser.parse_args()

    make_masks(args.ocean_mask, args.masks)

    make_areas(args.ocean_grid, args.areas)

    make_grids(args.ocean_grid, args.grids)


if __name__ == "__main__":
    sys.exit(main())


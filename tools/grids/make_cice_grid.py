#!/usr/bin/env python

import sys
import argparse
import netCDF4 as nc
import numpy as np

"""
Make a new CICE grid based on a MOM5 ocean grid.
"""

def calc_t_and_u_areas(ocn_area):

    tarea = np.zeros((ocn_area.shape[0]/2, ocn_area.shape[1]/2))
    uarea = np.zeros((ocn_area.shape[0]/2, ocn_area.shape[1]/2))

    tarea = tarea + ocn_area[0::2, 0::2]
    tarea = tarea + ocn_area[1::2, 0::2]
    tarea = tarea + ocn_area[1::2, 1::2]
    tarea = tarea + ocn_area[0::2, 1::2]

    # These need to wrap around the globe. Copy ocn_area and add an extra column at the end.
    ocn_area_ext = np.append(ocn_area[:], ocn_area[:, 0:1], axis=1)
    uarea = uarea + ocn_area_ext[0::2, 1::2]
    uarea = uarea + ocn_area_ext[1::2, 1::2]
    uarea = uarea + ocn_area_ext[1::2, 2::2]
    uarea = uarea + ocn_area_ext[0::2, 2::2]

    return tarea, uarea

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--ocean", help="The input ocean grid.", default='ocean_hgrid.nc')
    parser.add_argument("--ice", help="The output ice grid.", default='ice_grid.nc') 

    args = parser.parse_args()

    # Ocean grid. The new CICE grid is based on this.
    f_ocn = nc.Dataset(args.ocean, 'r')

    # New grid.
    f_ice_w = nc.Dataset(args.ice, 'w')

    # The ocean grid is double density.
    f_ice_w.createDimension('nx', len(f_ocn.dimensions['nx']) / 2)
    f_ice_w.createDimension('ny', len(f_ocn.dimensions['ny']) / 2)
    f_ice_w.createDimension('nc', 4)

    # All CICE grid variables. 
    ulat = f_ice_w.createVariable('ulat', 'f8', dimensions=('ny', 'nx'))
    ulat.units = "radians"
    ulat.title = "Latitude of U points"
    ulon = f_ice_w.createVariable('ulon', 'f8', dimensions=('ny', 'nx'))
    ulon.units = "radians"
    ulon.title = "Longitude of U points"
    tlat = f_ice_w.createVariable('tlat', 'f8', dimensions=('ny', 'nx'))
    tlat.units = "radians"
    tlat.title = "Latitude of T points"
    tlon = f_ice_w.createVariable('tlon', 'f8', dimensions=('ny', 'nx'))
    tlon.units = "radians"
    tlon.title = "Longitude of T points"
    htn = f_ice_w.createVariable('htn', 'f8', dimensions=('ny', 'nx'))
    htn.units = "cm"
    htn.title = "Width of T cells on North side."
    hte = f_ice_w.createVariable('hte', 'f8', dimensions=('ny', 'nx'))
    hte.units = "cm"
    hte.title = "Width of T cells on East side."
    angle = f_ice_w.createVariable('angle', 'f8', dimensions=('ny', 'nx'))
    angle.units = "radians"
    angle.title = "Rotation angle of U cells."
    angleT = f_ice_w.createVariable('angleT', 'f8', dimensions=('ny', 'nx'))
    angleT.units = "radians"
    angleT.title = "Rotation angle of T cells."
    tarea = f_ice_w.createVariable('tarea', 'f8', dimensions=('ny', 'nx'))
    tarea.units = "m^2"
    tarea.title = "Area of T cells."
    uarea = f_ice_w.createVariable('uarea', 'f8', dimensions=('ny', 'nx'))
    uarea.units = "m^2"
    uarea.title = "Area of U cells."
    lont_bonds = f_ice_w.createVariable('lont_bonds', 'f8', dimensions=('nc', 'ny', 'nx'))
    lont_bonds.units = "radians"
    lont_bonds.title = "Long. of T cell vertices."
    latt_bonds = f_ice_w.createVariable('latt_bonds', 'f8', dimensions=('nc', 'ny', 'nx'))
    latt_bonds.units = "radians"
    latt_bonds.title = "Lat. of T cell vertices."
    #lonu_bonds = f_ice_w.createVariable('lonu_bonds', 'f8', dimensions=('nc', 'ny', 'nx'))
    #uarea.units = "radians"
    #uarea.title = "Long. of U cell vertices."
    #latu_bonds = f_ice_w.createVariable('latu_bonds', 'f8', dimensions=('nc', 'ny', 'nx'))
    #uarea.units = "radians"
    #uarea.title = "Lat of U cell vertices."

    # Required ocean variables.
    y = np.copy(f_ocn.variables['y'])
    x = np.copy(f_ocn.variables['x'])
    dy = np.copy(f_ocn.variables['dy'])
    dx = np.copy(f_ocn.variables['dx'])
    angle_dx = np.copy(f_ocn.variables['angle_dx'])
    ocn_tarea = np.copy(f_ocn.variables['tarea'])
    ocn_area = np.copy(f_ocn.variables['area'])

    # Select points from double density grid. In some cases the Southern most U points are excluded.
    # Also the last (Eastern) U points, they are duplicates of the first. 
    ulat[:,:] = y[2::2,0:-1:2]
    ulon[:,:] = x[2::2,0:-1:2]
    tlat[:,:] = y[1::2,1::2]
    tlon[:,:] = x[1::2,1::2]

    htn[:,:] = dx[1::2,0::2]
    hte[:,:] = dy[0::2,0:-1:2]

    angle[:,:] = angle_dx[2::2,0:-1:2]
    angleT[:,:] = angle_dx[1::2,1::2]

    tarea[:], uarea[:] = calc_t_and_u_areas(ocn_area)
    # Check that calculated areas are the same as that found in the ocean grid.
    assert(np.allclose(tarea[:], ocn_tarea[:]))

    # Corner lons of T cells.
    lont_bonds[0,:,:] = x[0:-1:2,0:-1:2]
    lont_bonds[1,:,:] = x[0:-1:2,2::2]
    lont_bonds[2,:,:] = x[2::2,2::2]
    lont_bonds[3,:,:] = x[2::2,0:-1:2]

    # Corner lats of T cells.
    latt_bonds[0,:,:] = y[0:-1:2,0:-1:2]
    latt_bonds[1,:,:] = y[0:-1:2,2::2]
    latt_bonds[2,:,:] = y[2::2,2::2]
    latt_bonds[3,:,:] = y[2::2,0:-1:2]

    # Corner lons of U cells.
    #lonu_bonds[0,:,:] = 
    #lonu_bonds[1,:,:] = 
    #lonu_bonds[2,:,:] = 
    #lonu_bonds[3,:,:] = 

    # Corner lats of U cells.
    #latu_bonds[0,:,:] = 
    #latu_bonds[1,:,:] = 
    #latu_bonds[2,:,:] = 
    #latu_bonds[3,:,:] = 

    # Now convert units: degrees -> radians. 
    tlat[:] = np.deg2rad(tlat[:])
    tlon[:] = np.deg2rad(tlon[:])
    ulat[:] = np.deg2rad(ulat[:])
    ulon[:] = np.deg2rad(ulon[:])

    htn[:] = htn[:] * 100.
    hte[:] = hte[:] * 100.

    angle[:] = np.deg2rad(angle[:])
    angleT[:] = np.deg2rad(angleT[:])

    lont_bonds[:] = np.deg2rad(lont_bonds[:])
    latt_bonds[:] = np.deg2rad(latt_bonds[:])
    #lonu_bonds[:] = lonu_bonds[:] * (np.pi / 180.)
    #latu_bonds[:] = latu_bonds[:] * (np.pi / 180.)

    f_ice_w.close()

if __name__ == "__main__":
    sys.exit(main())

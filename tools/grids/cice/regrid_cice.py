#!/usr/bin/env python

import sys, os
import argparse
import ast
import ESMP
import netCDF4 as nc
import numpy as np

"""
Regrid CICE inputs, based on ESMP tutorial at:
http://www.earthsystemmodeling.org/python_releases/last_esmp/python_doc/html/index.html
"""

def find_nearest(a, val):
    """
    Index of element in array closest to the scalar value 'val'.
    """
    return np.abs(a[0,:,:] - val).argmin()

def build_analytic_field(field, grid, domask):
    '''
    PRECONDITIONS: An ESMP_Field has been created as 'field'.  'grid' has
                   been created and coordinates have been set on both the
                   center and corner stagger locations.  'mask' holds the 
                   masked values of 'grid'.\n
    POSTCONDITIONS: The 'field' has been initialized to an analytic field.\n
    RETURN VALUES: \n ESMP_Field :: field \n
    '''
    DEG2RAD = 3.141592653589793/180.0

    # get the field pointer
    fieldPtr = ESMP.ESMP_FieldGetPtr(field) 
     
    # get the grid bounds and coordinate pointers
    exLB, exUB = ESMP.ESMP_GridGetCoord(grid, ESMP.ESMP_STAGGERLOC_CENTER)

    # get the mask
    if domask:
        mask = ESMP.ESMP_GridGetItem(grid, item=ESMP.ESMP_GRIDITEM_MASK)

    # get the coordinate pointers and set the coordinates
    [x,y] = [0, 1]
    gridXCoord = ESMP.ESMP_GridGetCoordPtr(grid, x, ESMP.ESMP_STAGGERLOC_CENTER)
    gridYCoord = ESMP.ESMP_GridGetCoordPtr(grid, y, ESMP.ESMP_STAGGERLOC_CENTER)

    p = 0 
    for i1 in range(exLB[1], exUB[1]): 
        for i0 in range(exLB[0], exUB[0]): 
            theta = DEG2RAD*gridXCoord[p]
            phi = DEG2RAD*(90.0 - gridYCoord[p])
            fieldPtr[p] = 2.0 + np.cos(theta)**2 * np.cos(2.0*phi)
            p = p + 1

    '''
    theta = np.array(DEG2RAD*gridXCoord[:])
    phi = np.array(DEG2RAD*(90. - gridYCoord[:]))
    fieldPtr[:] = 2. + np.cos(theta[:])**2 * np.cos(2.*phi[:])
    '''
    return field


def compute_mass(valuefield, areafield, fracfield, dofrac):
    '''
    PRECONDITIONS: Two ESMP_Fields have been created and initialized.  'valuefield'
                   contains data values of a field built on the cells of a grid, 
                   'areafield' contains the areas associated with the grid 
                   cells, and 'fracfield' contains the fractions of each cell
                   which contributed to a regridding operation involving
                   'valuefield.  'dofrac' is a boolean value that gives the
                   option to not use the 'fracfield'.\n
    POSTCONDITIONS: The mass of the data field is computed and returned.\n
    RETURN VALUES: integer :: mass \n
    '''

    mass = 0.0
    ESMP.ESMP_FieldRegridGetArea(areafield)
    area = ESMP.ESMP_FieldGetPtr(areafield)
    value = ESMP.ESMP_FieldGetPtr(valuefield)
    frac = 0
    if dofrac:
        frac = ESMP.ESMP_FieldGetPtr(fracfield)

    for i in range(valuefield.size):
        if dofrac:
            mass += area[i]*value[i]*frac[i]
        else:
            mass += area[i]*value[i]

    return (mass, area)


def compare_fields(interp_field, exact_field, dstfracfield, srcmass, dstmass):
    '''
    PRECONDITIONS: 'interp_field' is a Field that holds the values resulting
                  from a regridding operation, 'exact_field' is a Field
                  containing the values of the exact solution that is 
                  expected, and 'dstfracfield' is a Field containing the
                  fractions of the 'interp_field' which contributed to the
                  regridding product.  'srcmass' and 'dstmass' are the 
                  mass values for the source and destination data fields. \n
    POSTCONDITIONS: The interpolation accuracy of a regridding operation is
                  determined by comparing the 'interp_field' to the 
                  'exact_field'.  The mass conservation is validated by
                  comparing the 'srcmass' to the 'dstmass'.\n
    RETURN VALUES: None \n
    '''

    vm = ESMP.ESMP_VMGetGlobal()
    localPet, _ = ESMP.ESMP_VMGet(vm)

    # get the data pointers for the fields
    interp = ESMP.ESMP_FieldGetPtr(interp_field)
    exact = ESMP.ESMP_FieldGetPtr(exact_field)
    dstfrac = ESMP.ESMP_FieldGetPtr(dstfracfield)

    if (interp_field.size != exact_field.size):
        raise TypeError('compare_fields: Fields must be the same size!')

    # initialize to True, and check for False point values
    total_error = 0.0
    max_error = 0.0
    min_error = 1000000.0
    for i in range(interp_field.size):
        if (exact[i] != 0.0):
            err = abs(interp[i]/dstfrac[i] - exact[i])/abs(exact[i])
        else:
            err = abs(interp[i]/dstfrac[i] - exact[i])
        total_error = total_error + err

        if (err > max_error): 
            max_error = err
        if (err < min_error): 
            min_error = err

    # check the mass
    csrv = False
    csrv_error = abs(dstmass - srcmass)/srcmass
    if (csrv_error < 10e-12):
       csrv = True
    itrp = False
    if (max_error < 10E-2):
        itrp = True

    if (itrp and csrv):
        print "PASS"
    else:
        print "FAIL"
    print "       Total error = "+str(total_error)
    print "       Max error   = "+str(max_error)
    print "       Min error   = "+str(min_error)
    print "       Csrv error  = "+str(csrv_error)
    print "       srcmass     = "+str(srcmass)
    print "       dstmass     = "+str(dstmass)
  
    return

def run_regridding(srcfield, dstfield, srcfracfield, dstfracfield):
    '''
    PRECONDITIONS: Two ESMP_Fields have been created and a regridding operation 
                   is desired from 'srcfield' to 'dstfield'.  The 'srcfracfield'
                   and 'dstfractfield' are Fields created to hold
                   the fractions of the source and destination fields which 
                   contribute to the regridding operation.\n
    POSTCONDITIONS: An ESMP regridding operation has set the data on 'dstfield', 
                    'srcfracfield', and 'dstfracfield'.\n
    RETURN VALUES: \n ESMP_Field :: dstfield \n ESMP_Field :: srcfracfield \n
                   ESMP_Field :: dstfracfield \n
    '''
    # call the regridding functions
    routehandle = ESMP.ESMP_FieldRegridStore(srcfield, dstfield,
                                             srcMaskValues=np.array([1], dtype=np.int32),
                                             dstMaskValues=np.array([1], dtype=np.int32),
                                             regridmethod=ESMP.ESMP_REGRIDMETHOD_CONSERVE,
                                             unmappedaction=ESMP.ESMP_UNMAPPEDACTION_ERROR,
                                             srcFracField=srcfracfield, 
                                             dstFracField=dstfracfield)
    ESMP.ESMP_FieldRegrid(srcfield, dstfield, routehandle)
    ESMP.ESMP_FieldRegridRelease(routehandle)

    return dstfield, srcfracfield, dstfracfield

def make_grid(field_def):
    """
    Define a grid

    Use the OASIS atm grid. 
    """

    f, lon_name, lat_name, clon_name, clat_name = field_def

    lons = np.copy(f.variables[lon_name])
    lons = np.rad2deg(lons)
    lats = np.copy(f.variables[lat_name])
    lats = np.rad2deg(lats)

    clons = np.copy(f.variables[clon_name])
    clons = np.rad2deg(clons)
    clats = np.copy(f.variables[clat_name])
    clats = np.rad2deg(clats)

    # Create a grid with 1 periodic dimension.
    grid = ESMP.ESMP_GridCreate1PeriDim(np.array((lons.shape[1], lons.shape[0]), dtype=np.int32))

    # Add centres to grid.
    ESMP.ESMP_GridAddCoord(grid, staggerloc=ESMP.ESMP_STAGGERLOC_CENTER)
    lb_center, ub_center = ESMP.ESMP_GridGetCoord(grid, ESMP.ESMP_STAGGERLOC_CENTER)

    [x, y] = [0, 1]
    x_center = ESMP.ESMP_GridGetCoordPtr(grid, x, ESMP.ESMP_STAGGERLOC_CENTER)
    y_center = ESMP.ESMP_GridGetCoordPtr(grid, y, ESMP.ESMP_STAGGERLOC_CENTER)
    x_center[:] = lons.flatten()
    y_center[:] = lats.flatten()

    # Add corners to grid. 
    ESMP.ESMP_GridAddCoord(grid, staggerloc=ESMP.ESMP_STAGGERLOC_CORNER)
    lb_corner, ub_corner = ESMP.ESMP_GridGetCoord(grid, ESMP.ESMP_STAGGERLOC_CORNER)
    nx, ny = ub_corner[:] - lb_corner[:]

    x_corner = ESMP.ESMP_GridGetCoordPtr(grid, x, ESMP.ESMP_STAGGERLOC_CORNER)
    x_corner[:] = np.NAN
    x_corner = x_corner.reshape(ny, nx)
    y_corner = ESMP.ESMP_GridGetCoordPtr(grid, y, ESMP.ESMP_STAGGERLOC_CORNER)
    y_corner[:] = np.NAN
    y_corner = y_corner.reshape(ny, nx)

    # Need to copy over the corners which are shape (4, 300, 360) to flat a (301, 360) 
    # array (for example). This is done by copying over all the corner 0 coordinates,
    # then fixing up the top row. 

    x_corner[:ny-1,:] = clons[0,:,:] 
    y_corner[:ny-1,:] = clats[0,:,:]

    assert (np.isnan(np.sum(x_corner)) and np.isnan(np.sum(y_corner)))

    x_corner[ny-1:,:] = clons[3,-1,:]
    y_corner[ny-1:,:] = clats[3,-1,:]

    x_corner = x_corner.reshape(ny*nx)
    y_corner = y_corner.reshape(ny*nx)

    x_corner = (x_corner + 360.) % 360.

    # Check that there are no NANs left.
    assert not (np.isnan(np.sum(x_corner)) or np.isnan(np.sum(y_corner)))

    return grid

def setup_grid_and_fields(src_def, dest_def):

    ESMP.ESMP_Initialize()
    ESMP.ESMP_LogSet(True)

    # Create source and destination grids.
    src_grid = make_grid(src_def)
    dest_grid = make_grid(dest_def)

    # Fields to regrid
    src_field = ESMP.ESMP_FieldCreateGrid(src_grid, 'src_field')
    dest_field = ESMP.ESMP_FieldCreateGrid(dest_grid, 'dest_field')

    # Area and fraction fields.
    src_frac = ESMP.ESMP_FieldCreateGrid(src_grid, 'src_frac')
    dest_frac = ESMP.ESMP_FieldCreateGrid(dest_grid, 'dest_frac')

    dest_area = ESMP.ESMP_FieldCreateGrid(dest_grid, 'dest_area')
    src_area = ESMP.ESMP_FieldCreateGrid(src_grid, 'src_area')

    return (src_grid, dest_grid, src_field, dest_field, src_frac, dest_frac, src_area, dest_area)

def test_regrid():
    """
    Check the OASIS grids by regridding and analytic function and comparing to the expected result.

    This does not pass, although close. Need to experiment with some different grid setups to see 
    what's going on. Leave this for now.
    """
    src_grid, dest_grid, src_field, dest_field, src_frac, dest_frac, src_area, dest_area = setup_grid_and_fields()

    dest_exact = ESMP.ESMP_FieldCreateGrid(dest_grid, 'dest_exact')

    # Intialise analytic test field.
    src_field = build_analytic_field(src_field, src_grid, False)
    dest_exact = build_analytic_field(dest_exact, dest_grid, False)

    # Do the regridding 
    dest_field, src_frac, dest_frac = run_regridding(src_field, dest_field, src_frac, dest_frac)

    # Compute mass
    src_mass, _ = compute_mass(src_field, src_area, src_frac, True)
    dest_mass, _ = compute_mass(dest_field, dest_area, 0, False)

    compare_fields(dest_field, dest_exact, dest_frac, src_mass, dest_mass)

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("src_grid", help="A Python tuple describing the source grid. \
                         The tuple is: filename, longitude field, latitude field, corner longitudes field , \
                         corner latitudes field.\"")
    parser.add_argument("dest_grid", help="A Python tuple describing the destination grid. \
                         It has the same format as the source grid argument.")
    parser.add_argument("fields", help="A Python list of field tuples describing fields to regrid. \
                         Each tuple is: source filename, field name, destination filename. E.g. \
                         %s \"('grid.nc', 'lons', 'lats', 'clons', 'clats')\" \
                         \"('grid.new.nc', 'lons', 'lats', 'clons', 'clats')\" \
                         \"[('core_runoff.nc', 'runoff', 'core_runoff.new.nc')]\". \
                         If the destination file does not exist it will be created. \
                         Don't forget the double and single quotes." % sys.argv[0])

    args = parser.parse_args()

    # Open src and dest grid files provided on the command line.
    args_src_grid = list(ast.literal_eval(args.src_grid))
    args_dest_grid = list(ast.literal_eval(args.dest_grid))
    src_grid_filename, src_lons, _, _, _ = args_src_grid
    dest_grid_filename, dest_lons, _, _, _ = args_dest_grid

    src_grid_file = nc.Dataset(src_grid_filename, 'r')
    dest_grid_file = nc.Dataset(dest_grid_filename, 'r')

    args_src_grid[0] = src_grid_file
    args_dest_grid[0] = dest_grid_file

    # Open up the source and destination grids and do setup.
    src_grid, dest_grid, src_field, dest_field, src_frac, dest_frac, src_area, dest_area = setup_grid_and_fields(args_src_grid, args_dest_grid)

    # Iterate over the each of the fields to be regridded.
    for src_file, field_name, dest_file in ast.literal_eval(args.fields):

        src_file = nc.Dataset(src_file, 'r')
        if os.path.exists(dest_file):
            dest_file = nc.Dataset(dest_file, 'r+')
        else:
            dest_file = nc.Dataset(dest_file, 'w')

        # Load the field to be regridded.
        src_field_ptr = ESMP.ESMP_FieldGetPtr(src_field) 
        # If field is 3d (i.e. has time) then just use the first time point.
        src_field_tmp = np.copy(src_file.variables[field_name])
        if len(src_field_tmp.shape) == 3:
            src_field_tmp = src_field_tmp[0,:,:]

        src_field_ptr[:] = ((src_field_tmp).reshape(src_field.size))[:]

        # Do the regridding 
        dest_field, src_frac, dest_frac = run_regridding(src_field, dest_field, src_frac, dest_frac)

        # Write out field.
        dest_shape = dest_grid_file.variables[dest_lons].shape
        dest_field_ptr = ESMP.ESMP_FieldGetPtr(dest_field)
        dest_field_ptr = dest_field_ptr.reshape(dest_shape)
        # Create dimensions if necessary.
        if not dest_file.dimensions.has_key('nx'):
            dest_file.createDimension('nx', dest_shape[1])
            dest_file.createDimension('ny', dest_shape[0])

        if not dest_file.variables.has_key(field_name):
            dest_file.createVariable(field_name, 'f8', ('ny', 'nx'))

        dest_file.variables[field_name][:,:] = dest_field_ptr[:,:] 

        # Check some results. 
        src_mass, src_area = compute_mass(src_field, src_area, src_frac, True)
        dest_mass, dest_area = compute_mass(dest_field, dest_area, 0, False)
        np.testing.assert_approx_equal(src_mass, dest_mass)

        src_file.close()
        dest_file.close()

    src_grid_file.close()
    dest_grid_file.close()


if __name__ == "__main__":
    sys.exit(main())

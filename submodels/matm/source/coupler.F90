
module coupler

use mod_oasis, only : oasis_init_comp, oasis_def_var, oasis_get_localcomm, &
                      oasis_def_partition, oasis_enddef, OASIS_OK, OASIS_REAL, &
                      OASIS_IN, OASIS_OUT
use error_handler , only : assert
use mpi, only : mpi_init, mpi_comm_size, mpi_comm_rank, MPI_SUCCESS

implicit none

private
public coupler_init, coupler_put, coupler_get, couple_field_type, MAX_COUPLING_FIELDS

type couple_field_type
    integer :: id
    character(len=8) :: name
    real, dimension(:,:), allocatable :: field
end type

integer, parameter :: BOX_PARTITION = 2, MAX_COUPLING_FIELDS = 20, MAX_FIELD_NAME_LEN = 8

! Namelist parameters
character(len=MAX_FIELD_NAME_LEN), dimension(MAX_COUPLING_FIELDS) :: in_field_names, out_field_names

namelist /coupling_setup/ in_field_names, out_field_names

contains 

subroutine read_field_info(xres, yres, in_fields, out_fields)

    integer, intent(in) :: xres, yres ! field resolution
    type(couple_field_type), dimension(:), allocatable, intent(out) :: in_fields, out_fields

    integer :: num_in, num_out, i, tmp_unit

    ! Read in coupling field information. 
    num_put = 0
    num_get = 0

    do i=1, MAX_COUPLING_FIELDS
        in_field_names(i) = ''
        out_field_names(i) = ''
    enddo

    open(newunit=tmp_unit, file='input_atm.nml')
    read(tmp_unit, nml=coupling_setup)
    close(tmp_unit)

    ! Count the coupling fields.
    do i=1, MAX_COUPLING_FIELDS
        if (len(trim(in_field_names(i))) /= 0) then
            num_in = num_in + 1
        endif
        if (len(trim(out_field_names(i))) /= 0) then
            num_out = num_out + 1
        endif
    enddo

    ! Initialise fields. 
    call assert(.not. allocated(in_fields), 'In fields already allocated')
    allocate(in_fields(num_in))  
    call assert(.not. allocated(out_fields), 'In fields already allocated')
    allocate(out_fields(num_out))

    do i=1, num_in
        in_fields(i)%name = in_field_names(i)
        allocate(in_fields(i)%field(xres, yres))
    enddo

    do i=1, num_out
        out_fields(i)%name = out_field_names(i)
        allocate(out_fields(i)%field(xres, yres))
    enddo

end subroutine

subroutine coupler_init(model_name, xglob, yglob, xloc, yloc, in_fields, out_fields) 

    character(len=*), intent(in) :: model_name
    ! global and local grid resolution 
    integer, intent(in) :: xglob, yglob, xloc, yloc
    type(couple_field_type), dimension(:), intent(inout) :: in_fields, out_fields

    integer :: ierror, i, local_comm
    ! Model id, partition id and description
    integer :: model_id, part_id, part_desc(5), var_actual_shape(4)
    ! Total PEs, my pe, my pe block/cell coords.
    integer :: npes, mype, xblock, yblock
    ! Temp array needed for call to oasis_def_var()
    integer, dimension(2) :: dims

    call assert(mod(xglob, xloc) == 0, "Global domain is not evenly divisible by local domain.")
    call assert(mod(yglob, yloc) == 0, "Global domain is not evenly divisible by local domain.")

    ! Initialise the fields arrays.
    call setup_fields(xloc, yloc, in_fields, out_fields)

    call mpi_init(ierror)
    call assert(ierror == MPI_SUCCESS, "mpi_init() failed.")

    call oasis_init_comp(model_id, model_name, ierror)
    call assert(ierror == OASIS_OK, "oasis_init_comp() failed.")

    ! Get local communicator. 
    call oasis_get_localcomm(local_comm, ierror)
    call assert(ierror == OASIS_OK, "oasis_get_localcomm() failed.")

    call mpi_comm_size(local_comm, npes, ierror)
    call assert(ierror == MPI_SUCCESS, "mpi_comm_size() failed.")
    call mpi_comm_rank(local_comm, mype, ierror)
    call assert(ierror == MPI_SUCCESS, "mpi_comm_rank() failed.")

    ! The block/cell coordinate of this pe.
    xblock = mype / (xglob / xloc)
    yblock = mype / (yglob / yloc)

    ! Define the partition that this proc is responsible for. We use a box 
    ! partition, each partition is a rectangular region of the global domain, 
    ! described by the offset of the upper left corner and the x and y extents.
    part_desc(1) = BOX_PARTITION
    ! Upper left corner global offset.
    part_desc(2) = (xglob * yloc * yblock) + (xloc * xblock) 
    part_desc(3) = xloc
    part_desc(4) = yloc
    part_desc(5) = xglob 

    call oasis_def_partition(part_id, part_desc, ierror)
    call assert(ierror == OASIS_OK, "oasis_def_partition() failed")

    var_actual_shape(1) = 1
    var_actual_shape(2) = part_desc(3)
    var_actual_shape(3) = 1
    var_actual_shape(4) = part_desc(4)

    ! Now define the variables.
    do i=1, size(in_fields)
        ! The number of dimensions of fields.
        dims(1) = size(shape(in_fields%fields))
        dims(2) = 1 ! Always one. 
        call oasis_def_var(in_fields(i)%id, in_fields(i)%name, part_id, dims, &
                           OASIS_IN, var_actual_shape, OASIS_REAL, ierror) 
        call assert(ierror == OASIS_OK, "oasis_def_var() failed")
    enddo

    do i=1, size(out_fields)
        dims(1) = size(shape(in_fields%fields))
        dims(2) = 1 ! Always one. 
        call oasis_def_var(out_fields(i)%id, out_fields(i)%name, part_id, dims, &
                           OASIS_OUT, var_actual_shape, OASIS_REAL, ierror) 
        call assert(ierror == OASIS_OK, "oasis_def_var() failed")
    enddo

    call oasis_enddef(ierror)
    call assert(ierror == OASIS_OK, "oasis_enddef() failed")

end subroutine

subroutine coupler_put() 

    ! Iterate over coupling fields and send all out fields.

end subroutine

subroutine coupler_get() 

    ! Iterate over coupling fields and get all in fields.

end subroutine

subroutine coupler_close()
    
    ! FIXME: iterate over coupling fields and deallocate internal memory.

    deallocate(coupling_fields)

end subroutine

end module 

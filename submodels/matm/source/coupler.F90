
module coupler

use mod_oasis, only : oasis_init_comp, oasis_def_var, oasis_get_localcomm, &
                      oasis_def_partition, oasis_enddef, OASIS_OK, OASIS_REAL, &
                      OASIS_IN, OASIS_OUT
use error_handler , only : assert
use mpi, only : mpi_init, mpi_comm_size, mpi_comm_rank, MPI_SUCCESS

implicit none

private
public coupler_init, coupler_put, coupler_get, couple_field_type

type couple_field_type
    integer :: id
    character(len=8) :: name
    character(len=256) :: file_name
    character(len=256) :: file_var_name
    integer :: dims
    integer :: direction
    integer :: xglob
    integer :: yglob
    real, dimension(:,:), allocatable :: field
end type

integer, parameter :: BOX_PARTITION = 2, MAX_FIELDS = 20, MAX_FIELD_NAME_LEN = 8

! Namelist parameters
character(len=MAX_FIELD_NAME_LEN), dimension(MAX_FIELDS) :: put_fields, get_fields

namelist /coupling_setup/ put_fields, get_fields

contains 

subroutine setup_fields(xres, yres, fields)

    integer, intent(in) :: xres, yres ! field resolution
    type(couple_field_type), dimension(:), pointer, intent(out) :: fields

    integer :: num_put, num_get, i

    ! Read in coupling field information. 
    num_put = 0
    num_get = 0

    do i=1, MAX_FIELDS
        put_fields(i) = ''
        get_fields(i) = ''
    enddo

    ! FIXME: allocate unit properly
    open(unit=1, file='input_atm.nml')
    read(unit=1, nml=coupling_setup)
    close(unit=1)

    do i=1, MAX_FIELDS
        if (len(trim(put_fields(i))) /= 0) then
            num_put = num_put + 1
        endif
        if (len(trim(get_fields(i))) /= 0) then
            num_get = num_get + 1
        endif
    enddo

    ! FIXME: check that fields is not already allocated.
    ! Initialise fields. 
    allocate(fields(num_put + num_get))  

    do i=1, num_put
        coupling_fields(i)%name = put_fields(i)
        coupling_fields(i)%dims = 2
        coupling_fields(i)%xres = xres
        coupling_fields(i)%yres = yres
        coupling_fields(i)%direction = OASIS_OUT
        allocate(coupling_fields(i)%field(xres, yres))
    enddo

    do i=i, num_get
        coupling_fields(i)%name = get_fields(i)
        coupling_fields(i)%dims = 2
        coupling_fields(i)%xglob = xres
        coupling_fields(i)%yglob = yres
        coupling_fields(i)%direction = OASIS_IN
        allocate(coupling_fields(i)%field(xres, yres))
    enddo

end subroutine

subroutine coupler_init(model_name, xglob, yglob, xloc, yloc, fields) 

    character(len=*), intent(in) :: model_name
    ! global and local grid resolution 
    integer, intent(in) :: xglob, yglob, xloc, yloc
    type(couple_field_type), dimension(:), intent(inout) :: fields

    integer :: ierror, i, local_comm
    ! Model id, partition id and description
    integer :: model_id, part_id, part_desc(5)
    ! Total PEs, my pe, my pe block/cell coords.
    integer :: npes, mype, xblock, yblock
    ! Temp array needed for call to oasis_def_var()
    integer, dimension(2) :: dims

    call assert(mod(xglob, xloc) == 0, "Global domain is not evenly divisible by local domain.")
    call assert(mod(yglob, yloc) == 0, "Global domain is not evenly divisible by local domain.")

    ! Initialise the fields array.
    call setup_fields(xres, yres, fields)

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

    ! Now define the variables.
    do i=1, size(fields)
        dims(1) = fields(i)%dims 
        dims(2) = 1 ! Always one. 
        call oasis_def_var(fields(i)%id, fields(i)%name, part_id, dims, &
                           fields(i)%direction, fields(i)%shape, OASIS_REAL, ierror) 
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

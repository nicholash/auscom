
module coupler

use mod_oasis, only : oasis_init_comp, oasis_def_var, oasis_get_localcomm, &
                      oasis_def_partition, oasis_enddef, OASIS_OK, OASIS_REAL, &
                      OASIS_IN, OASIS_OUT, oasis_put, oasis_get
use error_handler , only : assert
use mpi, only : mpi_init, mpi_comm_size, mpi_comm_rank, MPI_SUCCESS

implicit none

private
public coupler_init, coupler_put, coupler_get, coupler_close, couple_field_type

! Type declarations. 
type couple_field_type
    integer :: id
    integer :: direction 
    character(len=8) :: name
    real, dimension(:,:), allocatable :: field
end type

integer, parameter :: BOX_PARTITION = 2, COUPLER_OUT = OASIS_OUT, COUPLER_IN = OASIS_IN

integer :: model_id, part_id
! Global and local grid resolution 
integer :: x_global_res, y_global_res, x_local_res, y_local_res
integer :: coupler_initialised = .false.

contains 

subroutine coupler_add_field(field, field_name, direction)

    type(couple_field_type), intent(inout) :: field
    character(len=*), intent(in) :: field_name
    integer, intent(in) :: direction

    ! Temp arrays needed for call to oasis_def_var()
    integer, dimension(2) :: dims
    integer, dimension(4) :: field_shape

    call assert(direction == COUPLER_OUT .or. direction == COUPLER_IN,
                'Bad coupling field direction')
    call assert(coupler_initialised, 'coupler_add_field() called before coupler_init()')

    call assert(.not. allocated(field%field), 'Field data already allocated')
    allocate(field%field(x_res, y_res))
    field%direction = direction

    ! The shape of the field.
    field_shape(1) = 1
    field_shape(2) = x_local_res
    field_shape(3) = 1
    field_shape(4) = y_local_res

    ! The number of dimensions of the field.
    dims(1) = size(shape(field(i)%field))
    dims(2) = 1 ! Always one. 

    ! Define the field.
    call oasis_def_var(field(i)%id, field(i)%name, partition_id, dims, &
                       fields(i)%direction, field_shape, OASIS_REAL, ierror) 
    call assert(ierror == OASIS_OK, "oasis_def_var() failed")

end subroutine coupler_add_field

subroutine coupler_init(model_name, xglob, yglob, xloc, yloc) 

    character(len=*), intent(in) :: model_name
    integer, intent(in) :: xglob, yglob, xloc, yloc

    integer :: ierror, local_comm
    ! Total PEs, my pe, my pe block/cell coords.
    integer :: npes, mype, xblock, yblock
    integer :: part_desc(5)

    ! Save as module level variables.
    x_global_res = xglob
    y_global_res = xglob
    x_local_res = xloc
    y_local_res = yloc

    call assert(mod(xglob, xloc) == 0, "Global domain is not evenly divisible by local domain.")
    call assert(mod(yglob, yloc) == 0, "Global domain is not evenly divisible by local domain.")

    ! Initialise the fields arrays.
    call read_field_info(xloc, yloc, in_fields, out_fields)

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

    coupler_initialised = .true.

end subroutine

subroutine coupler_init_done()

    integer :: ierror

    call assert(coupler_initialised, 'coupler_init_done() called before coupler_init()')

    call oasis_enddef(ierror)
    call assert(ierror == OASIS_OK, "oasis_enddef() failed")

end subroutine coupler_init_done

subroutine coupler_put(time, fields) 

    integer, intent(in) :: time
    type(couple_field_type), dimension(:), intent(inout) :: fields

    integer :: i, info

    call assert(coupler_initialised, 'coupler_put() called before coupler_init()')

    ! Iterate over coupling fields and send all out fields.
    do i=1, size(fields)
        call assert(fields(i)%direction == COUPLER_OUT, 'Called coupler_put() on non-output field')
        call oasis_put(fields(i)%id, time, fields(i)%field, info)
    enddo

end subroutine

subroutine coupler_get(time, fields) 

    integer, intent(in) :: time
    type(couple_field_type), dimension(:), intent(inout) :: fields

    integer :: i, info

    call assert(coupler_initialised, 'coupler_get() called before coupler_init()')

    ! Iterate over coupling fields and get all in fields.
    do i=1, size(fields)
        call assert(fields(i)%direction == COUPLER_OUT, 'Called coupler_get() on non-input field')
        call oasis_get(fields(i)%id, time, fields(i)%field, info)
    enddo

end subroutine

subroutine coupler_destroy_field(field)

    type(couple_field_type), intent(inout) :: field

    deallocate(field(i)%field)

end subroutine coupler_destroy_fields(fields)

subroutine coupler_close()
end subroutine

end module 

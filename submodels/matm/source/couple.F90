
module couple

use mod_oasis, only : oasis_init_comp, OASIS_OK
use error_handling, only : assert

implicit none
include "mpif.h"

private
public couple_init, couple_var_type

type couple_var_type
    integer :: id
    character(len=8) :: name
    integer :: dims
    integer :: direction
    integer, dimension(4) :: shape 
end type

integer, parameter :: BOX_PARTITION = 2

contains 

subroutine couple_init(model_name, iglob, jglob, iloc, jloc, vars) 

    character(len=*), intent(in) :: model_name

    ! global and local grid resolution 
    integer, intent(in) :: iglob, jglob, iloc, jloc 
    type(couple_var_type), dimension(:), intent(in) :: vars

    integer :: ierror, local_comm
    ! Model id, partition id and description
    integer :: model_id, part_id, part_desc(5)
    ! Total PEs, my pe, my pe block/cell coords.
    integer :: npes, mype, iblock, jblock
    ! Temp array needed for call to oasis_def_var()
    integer, dimenstion(2) :: dims

    call assert((iglob % iloc) /= 0, "Global domain is not evenly divisible by local domain.")
    call assert((jglob % jloc) /= 0, "Global domain is not evenly divisible by local domain.")

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
    iblock = mype / (iglob / iloc)
    jblock = mype / (jglob / jloc)

    ! Define the partition that this proc is responsible for. We use a box 
    ! partition, each partition is a rectangular region of the global domain, 
    ! described by the offset of the upper left corner and the x and y extents.
    partition_desc(1) = BOX_PARTITION
    ! Upper left corner global offset.
    part_desc(2) = (iglob * jloc * jpe) + (iloc * ipe) 
    part_desc(3) = iloc
    part_desc(4) = jloc
    part_desc(5) = iglob

    call oasis_def_partition(part_id, part_desc, ierror)
    call assert(ierror == OASIS_OK, "oasis_def_partition() failed")

    ! Now define the variables.
    do i=1, size(vars)
        dims(1) = vars(i)%dims 
        dims(2) = 1 ! Always one. 
        call oasis_def_var(vars(i)%id, vars(i)%name, part_id, dims, &
                           vars(i)%direction, vars(i)%shape, OASIS_REAL, ierror) 
        call assert(ierror == OASIS_OK, "oasis_def_var() failed")
    enddo

    call oasis_enddef(ierror)
    call assert(ierror == OASIS_OK, "oasis_enddef() failed")

end subroutine

end module 

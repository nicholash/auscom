
module data_loader

! Load the coupling field arrays with data from the CORE2 dataset. 

use netcdf
use calendar, only : date
use coupler, only : couple_field_type

implicit none

private
public init_data_loader, load_data

contains 

subroutine load_data(curr_time, coupling_fields)

    integer, intent(in) :: curr_time 
    type(couple_field_type), dimension(:), intent(inout) :: coupling_fields

    integer :: i, status, ncid, varid
    integer, dimension(3) :: start, count

    do i=1, size(coupling_fields)
        ! Open file
        status = nf90_open(coupling_fields(i)%file_name, NF90_NOWRITE, ncid)
        call assert(status /= NF90_NOERR, nf90_strerror(status))

        ! Get var reference 
        status = nf90_inq_varid(ncid, coupling_fields(i)%file_var_name, varid)
        call assert(status /= NF90_NOERR, nf90_strerror(status))

        count = (/ coupling_fields(i)%yglob, coupling_fields(i)%xglob, 1 /)
        start = (/ 1, 1, /)

        ! Read data
        status = nf90_get_var(ncid, varid, coupling_fields(i)%field, start=start, count=count)
        call assert(status /= NF90_NOERR, nf90_strerror(status))
    enddo
   
end subroutine

end module


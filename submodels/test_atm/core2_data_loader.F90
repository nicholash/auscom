
module core2_loader

use coupler, only : couple_field_type, MAX_COUPLING_FIELDS
use map, only : map_type, map_element_type
use error_handler, only : assert
use calendar, only : SECONDS_PER_YEAR

implicit none

private
public loader_init, loader_load

character(len=256), dimension(3, MAX_COUPLING_FIELDS) :: fields_to_files
namelist /core2_loader/ fields_to_files

contains

subroutine loader_init(out_fields)

    type(couple_field_type), dimension(:), intent(in) :: out_fields

    integer :: i, j, tmp_unit, num_out_fields
    type(map_type) :: fields_to_file_map
    type(map_element_type) :: elem
    logical :: found

    call assert(allocated(out_fields), 'loader_init(): out_fields not allocated.')

    do j, MAX_COUPLING_FIELDS
        do i, 3
            fields_to_files(i, j) = ''
        enddo
    enddo

    open(newunit=tmp_unit, file='input_atm.nml')
    read(tmp_unit, nml=core2_loader)
    close(tmp_unit)

    num_out_fields = 0
    do j, MAX_COUPLING_FIELDS
        if (len(trim(fields_to_files(1, j))) /= 0) then
            call assert(len(trim(fields_to_files(2, j) /= 0, 'Bad fields to files mapping')))
            call assert(len(trim(fields_to_files(3, j) /= 0, 'Bad fields to files mapping')))
            num_out_fields = num_out_fields + 1
        endif
    enddo

    call assert(len(out_fields) == num_out_fields, &
                'core2 inputs does not agree with coupling fields array.')

    ! Initialise the variable name -> file, var mapping.
    call fields_to_file_map%init()

    ! Associate each coupling field with an input source (netcdf file and variable).
    do i, num_out_fields
        elem%file_name = fields_to_files(2, i)
        elem%var_name = fields_to_files(3, i)
        call fields_to_file_map%put(fields_to_files(1, i), elem)
    enddo

    ! For all coupling fields, check that there is an associated file and var
    do i, size(out_fields)
        call fields_to_file_map%get(trim(out_fields(i)%name), elem, found)
        call assert(found, 'core2 inputs does not agree with coupling fields array.')
    enddo

end subroutine

subroutine loader_load(curr_time, out_fields)

    integer, intent(in) :: curr_time 
    type(couple_field_type), dimension(:), intent(inout) :: out_fields

    integer :: i, status, ncid, varid
    integer, dimension(3) :: start, count

    ! This dataset repeats every year.
    curr_time = mod(curr_time, SECONDS_PER_YEAR)
    ! It is a 6 hourly data set.
    curr_time = curr_time / (3600*6)

    do i=1, size(coupling_fields)

        ! Open file
        status = nf90_open(coupling_fields(i)%file_name, NF90_NOWRITE, ncid)
        call assert(status /= NF90_NOERR, nf90_strerror(status))

        ! Get var reference 
        status = nf90_inq_varid(ncid, coupling_fields(i)%file_var_name, varid)
        call assert(status /= NF90_NOERR, nf90_strerror(status))

        count = (/ coupling_fields(i)%field, coupling_fields(i)%field, 1 /)
        start = (/ 1, 1, curr_time /)

        ! Read data
        status = nf90_get_var(ncid, varid, coupling_fields(i)%field, start=start, count=count)
        call assert(status /= NF90_NOERR, nf90_strerror(status))
    enddo

end subroutine

subroutine loader_close()
end subroutine

end module

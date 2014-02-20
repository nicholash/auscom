
module core2_loader

use coupler, only : couple_field_type, MAX_COUPLING_FIELDS
use map, only : map_type, map_element_type
use error_handler, only : assert
use calendar, only : SECONDS_PER_YEAR
use netcdf, only : NF90_NOERR, NF90_NOWRITE, nf90_open, nf90_inq_varid, &
                   nf90_get_var, nf90_strerror

implicit none

private
public loader_init, loader_load, loader_close

type(map_type) :: fields_to_file_map
character(len=256), dimension(3, MAX_COUPLING_FIELDS) :: fields_to_files
namelist /core2_loader_nml/ fields_to_files

contains

subroutine loader_init(out_fields)

    type(couple_field_type), dimension(:), allocatable, intent(in) :: out_fields

    integer :: i, j, tmp_unit, num_out_fields
    type(map_element_type) :: elem
    logical :: found

    call assert(allocated(out_fields), 'loader_init(): out_fields not allocated.')

    do j=1, MAX_COUPLING_FIELDS
        do i=1, 3
            fields_to_files(i, j) = ''
        enddo
    enddo

    open(newunit=tmp_unit, file='input_atm.nml')
    read(tmp_unit, nml=core2_loader_nml)
    close(tmp_unit)

    num_out_fields = 0
    do j=1, MAX_COUPLING_FIELDS
        if (len(trim(fields_to_files(1, j))) /= 0) then
            call assert(len(trim(fields_to_files(2, j))) /= 0, 'Bad fields to files mapping')
            call assert(len(trim(fields_to_files(3, j))) /= 0, 'Bad fields to files mapping')
            num_out_fields = num_out_fields + 1
        endif
    enddo

    call assert(size(out_fields) == num_out_fields, &
                'Core2 inputs does not agree with coupling fields array.')

    ! Initialise the variable name -> file, var mapping.
    call fields_to_file_map%init()

    ! Associate each coupling field with an input source (netcdf file and variable).
    do i=1, num_out_fields
        elem%file_name = fields_to_files(2, i)
        elem%var_name = fields_to_files(3, i)
        call fields_to_file_map%put(fields_to_files(1, i), elem)
    enddo

    ! For all coupling fields, check that there is an associated file and var
    do i=1, size(out_fields)
        call fields_to_file_map%get(trim(out_fields(i)%name), elem, found)
        call assert(found, 'Core2 inputs does not agree with coupling fields array.')
    enddo

end subroutine

subroutine loader_load(curr_time, out_fields)

    integer, intent(in) :: curr_time 
    type(couple_field_type), dimension(:), allocatable, intent(inout) :: out_fields

    type(map_element_type) :: map_elem
    integer :: i, status, ncid, varid, time
    integer, dimension(3) :: start, count
    logical :: found

    ! This dataset repeats every year.
    time = mod(curr_time, SECONDS_PER_YEAR)
    ! It is a 6 hourly data set.
    time = time / (3600*6)

    do i=1, size(out_fields)

        found = .false.
        call fields_to_file_map%get(trim(out_fields(i)%name), map_elem, found)
        call assert(found, 'Could not get file, var mapping for field name')

        ! Open file
        status = nf90_open(map_elem%file_name, NF90_NOWRITE, ncid)
        call assert(status /= NF90_NOERR, nf90_strerror(status))

        ! Get var reference 
        status = nf90_inq_varid(ncid, map_elem%var_name, varid)
        call assert(status /= NF90_NOERR, nf90_strerror(status))

        count = (/ size(out_fields(i)%field), size(out_fields(i)%field), 1 /)
        start = (/ 1, 1, time /)

        ! Read data
        status = nf90_get_var(ncid, varid, out_fields(i)%field, start=start, count=count)
        call assert(status /= NF90_NOERR, nf90_strerror(status))
    enddo

end subroutine

subroutine loader_close()
    ! Do nothing.
end subroutine

end module

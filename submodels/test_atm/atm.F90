
program atm

use coupler, only : coupler_init, coupler_get, coupler_put, coupler_close, couple_field_type
use core2_loader , only : loader_init, loader_load, loader_close
use test, only : run_tests
use calendar, only : calendar_timediff, date_type, calendar_make_date
use error_handler, only : assert

implicit none

integer, parameter  MAX_COUPLING_FIELDS = 20, MAX_FIELD_NAME_LEN = 8

! Namelist parameters
integer, dimension(3) :: exp_start_date, run_start_date, run_end_date
integer :: dt = 1800
integer, dimension(2) :: resolution
character(len=MAX_FIELD_NAME_LEN), dimension(MAX_COUPLING_FIELDS) :: from_ice_field_names = '', to_ice_field_names = ''

namelist /atm_config/ exp_start_date, run_start_date, run_end_date, dt, resolution, &
                      from_ice_field_names, to_ice_field_names

    type(couple_field_type), dimension(:), allocatable :: from_ice_fields, to_ice_fields
    type(date_type) :: start_date, end_date
    integer :: step, nsteps
    integer :: x_global_res, y_global_res, x_local_res, y_local_res
    integer :: runtime, curr_time
    integer :: tmp_unit, num_from_ice_fields, num_to_ice_fields, i

    x_global_res = resolution(1)
    y_global_res = resolution(2)
    x_local_res = x_global_res
    y_local_res = y_global_res
    
    ! Create date types.
    call calendar_make_date(run_start_date, start_date)
    call calendar_make_date(run_end_date, end_date)

    ! Read namelist which includes information about the start and end date,
    ! model resolution and names and direction of coupling fields. 
    open(newunit=tmp_unit, file='input_atm.nml')
    read(tmp_unit, nml=coupler_nml)
    close(tmp_unit)

    ! Count the coupling fields
    num_from_ice_fields = 0
    num_to_ice_fields = 0
    do i=1, MAX_COUPLING_FIELDS
        if (from_ice_field_names(i) /= '') then
            num_from_ice_fields += 1
        endif
        if (to_ice_field_names(i) /= '') then
            num_to_ice_fields += 1
        endif
    enddo

    ! Initialise the coupler. 
    call coupler_init('atmxxx', xglob, yglob, xloc, yloc, fields)

    ! Create/add the coupling fields. 
    allocate(from_ice_fields(num_from_ice_fields))
    allocate(to_ice_fields(num_to_ice_fields))
    do i=1, num_from_ice_fields
        call coupler_add_field(from_ice_fields(i), from_ice_field_names(i), COUPLER_IN)
    enddo
    do i=1, num_to_ice_fields
        call coupler_add_field(to_ice_fields(i), to_ice_field_names(i), COUPLER_OUT)
    enddo

    call coupler_init_done()

    ! Init the data loader. Depending on the data source, this associates 
    ! a coupling field with a model or data field.
    call loader_init(to_ice_fields)

    ! Calculate time difference in seconds between start and end dates.
    call calendar_timediff(start_date, end_date, runtime)

    nsteps = runtime / dt
    curr_time = 0

    do step=1, nsteps 

        ! Get fields from coupler and write out. 
        call coupler_get(curr_time, from_ice_fields)

        ! Read forcing data from file, copy to coupling field
        call loader_load(curr_time, out_fields)

        ! Send fields to coupler.
        call coupler_put(curr_time, to_ice_fields)

        curr_time = curr_time + dt

    enddo

    ! Clean up.
    do i=1, num_from_ice_fields
        call coupler_destroy_field(from_ice_fields(i))
    enddo
    do i=1, num_to_ice_fields
        call coupler_destroy_field(to_ice_fields(i))
    enddo
    deallocate(from_ice_fields)
    deallocate(to_ice_fields)

    call coupler_close(in_fields, out_fields)
    call loader_close()

end program


program atm

use coupler, only : coupler_init, coupler_get, coupler_put, coupler_close, couple_field_type, &
                    COUPLER_MAX_FIELDS, COUPLER_MAX_FIELD_NAME_LEN
use core2_loader , only : loader_init, loader_load, loader_close
use test, only : run_tests
use calendar, only : calendar_timediff, date_type, calendar_make_date
use error_handler, only : assert

implicit none

! Namelist parameters
integer, dimension(3) :: run_start_date, run_end_date
integer :: dt = 1800
integer, dimension(2) :: resolution
integer, dimension(2) :: subdomain_decomposition
character(len=COUPLER_MAX_FIELD_NAME_LEN), dimension(COUPLER_MAX_FIELDS) :: from_ice_field_names = '', to_ice_field_names = ''

namelist /atm_config_nml/ run_start_date, run_end_date, dt, resolution, subdomain_decomposition &
                      from_ice_field_names, to_ice_field_names

    type(couple_field_type), dimension(:), allocatable :: from_ice_fields, to_ice_fields
    type(date_type) :: start_date, end_date
    integer :: step, nsteps
    integer :: x_global_res, y_global_res, x_subdomains, y_subdomains
    integer :: runtime, curr_time
    integer :: tmp_unit, num_from_ice_fields, num_to_ice_fields, i

    ! Read namelist which includes information about the start and end date,
    ! model resolution and names and direction of coupling fields. 
    open(newunit=tmp_unit, file='input_atm.nml')
    read(tmp_unit, nml=atm_config_nml)
    close(tmp_unit)

    x_global_res = resolution(1)
    y_global_res = resolution(2)
    x_subdomains = subdomain_decomposition(1)
    y_subdomains = subdomain_decomposition(2)
    
    ! Create date types.
    call calendar_make_date(run_start_date, start_date)
    call calendar_make_date(run_end_date, end_date)

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
    call coupler_init('atmxxx', x_global_res, y_global_res, x_subdomains, y_subdomains)

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

    call coupler_close()
    call loader_close()

end program

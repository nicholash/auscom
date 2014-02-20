
program atm

use coupler, only : coupler_init, coupler_get, coupler_put, coupler_close, couple_field_type
use core2_loader , only : loader_init, loader_load, loader_close
use test, only : run_tests
use calendar, only : calendar_timediff, date_type, calendar_make_date
use error_handler, only : assert

implicit none

! Namelist parameters
integer, dimension(3) :: exp_start_date, run_start_date, run_end_date
integer :: dt = 1800
integer, dimension(2) :: resolution

namelist /atm_config/ exp_start_date, run_start_date, run_end_date, dt, resolution

    type(couple_field_type), dimension(:), allocatable :: in_fields, out_fields
    type(date_type) :: start_date, end_date
    integer :: step, nsteps
    integer :: xglob, yglob, xloc, yloc 
    integer :: runtime, curr_time

    call run_tests()

    xglob = resolution(1)
    yglob = resolution(2)
    xloc = xglob
    yloc = yglob
    
    ! Create date types.
    call calendar_make_date(run_start_date, start_date)
    call calendar_make_date(run_end_date, end_date)

    ! Initialise the coupler. 
    call coupler_init('atmxxx', xglob, yglob, xloc, yloc, in_fields, out_fields)

    ! Init the data loader. Depending on the data source, this associates 
    ! a coupling field with a model or data field.
    call loader_init(out_fields)

    ! Calculate time difference in seconds between start and end dates.
    call calendar_timediff(start_date, end_date, runtime)

    nsteps = runtime / dt
    curr_time = 0

    do step=1, nsteps 

        ! Get fields from coupler and write out. 
        call coupler_get(curr_time, in_fields)

        ! Read forcing data from file, copy to coupling field
        call loader_load(curr_time, out_fields)

        ! Send fields to coupler.
        call coupler_put(curr_time, out_fields)

        curr_time = curr_time + dt

    enddo

    ! Clean up.
    call coupler_close(in_fields, out_fields)
    call loader_close()

end program

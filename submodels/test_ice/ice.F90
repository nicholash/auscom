
program ice

use coupler, only : coupler_init, coupler_get, coupler_put, coupler_close, couple_field_type
use calendar, only : calendar_timediff, date_type, calendar_make_date
use error_handler, only : assert

implicit none

! Namelist parameters
integer, dimension(3) :: exp_start_date, run_start_date, run_end_date
integer :: dt = 1800
integer, dimension(2) :: resolution

namelist /ice_config/ exp_start_date, run_start_date, run_end_date, dt, resolution

    type(couple_field_type), dimension(:), allocatable :: in_fields, out_fields
    type(date_type) :: start_date, end_date
    integer :: step, nsteps
    integer :: xglob, yglob, xloc, yloc 
    integer :: runtime, curr_time

    xglob = resolution(1)
    yglob = resolution(2)
    xloc = xglob
    yloc = yglob
    
    ! Create date types.
    call calendar_make_date(run_start_date, start_date)
    call calendar_make_date(run_end_date, end_date)

    ! Initialise the coupler. 
    call coupler_init('icexxx', xglob, yglob, xloc, yloc, in_fields, out_fields)

    ! Calculate time difference in seconds between start and end dates.
    call calendar_timediff(start_date, end_date, runtime)

    nsteps = runtime / dt
    curr_time = 0

    do step=1, nsteps 

        ! Get fields from atmos
        call coupler_get(curr_time, in_fields)

        ! Get fields from ocean
        call coupler_get(curr_time, in_fields)

        ! Do some calculation. 

        ! Send fields to ocean.
        call coupler_put(curr_time, out_fields)

        ! Send fields to atm.
        call coupler_put(curr_time, out_fields)

        curr_time = curr_time + dt

    enddo

    ! Clean up.
    call coupler_close(in_fields, out_fields)

end program

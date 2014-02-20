
program atm

use couple, only : coupler_init, coupler_setup_fields, coupler_get, coupler_put, couple_field_type
use core2_data_setup, only : init_data_loader, load_data
use test, only : run_tests
use calendar, only : get_runtime, date
use error_handler, only : assert

implicit none

! Namelist parameters
integer, dimension(3) :: exp_start_date, run_start_date, run_end_date
integer :: dt
integer, dimension(2) :: resolution

namelist /atm_config/ exp_start_date, run_start_date, run_end_date, dt, resolution

    type(couple_field_type), dimension(:), allocatable :: coupling_fields
    type(date) :: start_date, end_date
    integer :: step, nsteps
    integer :: xglob, yglob, xloc, yloc 
    integer :: runtime, curr_time

    call run_tests()

    xglob = resolution(1)
    yglob = resolution(2)
    xloc = xglob
    yloc = yglob
    
    start_date%year = run_start_date(1)
    start_date%month = run_start_date(2)
    start_date%day = run_start_date(3)

    end_date%year = run_end_date(1)
    end_date%month = run_end_date(2)
    end_date%day = run_end_date(3)

    ! Set up coupling variables. 
    ! FIXME: why not call this from coupler_init()?
    call coupler_setup_fields(coupling_fields, xglob, yglob)

    ! Initialise the coupler. 
    call coupler_init('atmxxx', xglob, yglob, xloc, yloc, coupling_fields)

    ! Once the coupler is initialised, init the data loader. 
    loader_init(coupling_fields)

    ! Figure out the runtime and start coupling loop. 
    call get_runtime(start_date, end_date, runtime)

    nsteps = runtime / dt
    curr_time = 0

    do step=1, nsteps 

        curr_time = curr_time + dt

        ! Get fields from coupler and write out. 
        call coupler_get(coupling_fields)

        ! Read forcing data from file, copy to coupling field
        call loader_load(curr_time, coupling_fields)

        ! Send fields to coupler.
        call coupler_put(coupling_fields)

    enddo

    ! Clean up.
    coupler_close(coupling_fields)

end program

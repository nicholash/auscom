
program atm

use couple, only : couple_init, couple_var_type

implicit none

    ! Define coupling variables.

    
    ! Set up the coupler. 
    call couple_init('atmxxx')

    ! Figure out the runtime and start coupling loop. 
    do step, nsteps 

        ! Get fields from coupler and write out. 

        ! Read forcing data from file.

        ! Send fields to coupler.

    enddo

    ! Clean up.

end program

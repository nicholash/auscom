module error_handler

use, intrinsic :: iso_fortran_env, only : error_unit

#if defined(__INTEL_COMPILER)
use ifcore
use ifport
use mpi
#endif

implicit none

private
public assert
#if defined(__INTEL_COMPILER)
public error_handler_fpe_traceback, error_handler_mpi_traceback
#endif

contains

subroutine assert(res, error_msg)
    
    logical, intent(in) :: res
    character(len=*), intent(in) :: error_msg

    if (.not. res) then
        print *, 'Error: '//error_msg
        !write(error_unit, error_msg)
        call exit(1)
    endif

end subroutine

#if defined(__INTEL_COMPILER)

subroutine do_mpi_traceback(comm, err_code)

    integer, intent(in) :: comm, err_code
    integer :: ierr, rank
    character(len=12) :: rank_str

    call MPI_Comm_rank(MPI_COMM_WORLD, rank, ierr)
    write (rank_str, '(i12)') rank

    call tracebackqq('MPI traceback error handler called by rank: '//rank_str)
    call MPI_Abort(comm, err_code, ierr)
end subroutine

subroutine do_fpe_traceback(signal, code)
    integer, intent(in) :: signal, code

    character(len=128) :: error_type

    select case(code)
        case (fpe$invalid)
            error_type = 'Invalid operation'
        case (fpe$zerodivide)
            error_type = 'Divide-by-zero'
        case (fpe$overflow)
            error_type = 'Numeric overflow'
        case (fpe$underflow)
            error_type = 'Numeric underflow'
        case (fpe$inexact)
            error_type = 'Inexact result (precision)'
    end select

    call tracebackqq('FPE exception: '//trim(error_type))
    stop 'FPE handler called'

end subroutine

subroutine error_handler_fpe_traceback

    integer :: ret

    ret = ieee_handler('set', 'overflow', do_fpe_traceback)
    ret = ieee_handler('set', 'division', do_fpe_traceback)
    ret = ieee_handler('set', 'invalid', do_fpe_traceback)

end subroutine

subroutine error_handler_mpi_traceback

    integer :: ierr
    integer :: traceback_handler

    call MPI_Comm_create_errhandler(traceback_err_handler, do_mpi_traceback, ierr)
    call MPI_Comm_set_errhandler(MPI_COMM_WORLD, do_mpi_traceback, ierr)

end subroutine

! defined(__INTEL_COMPILER)
#endif

end module

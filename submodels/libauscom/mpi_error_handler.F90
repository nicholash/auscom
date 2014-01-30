
module mpi_error_handler

    use ifcore
    include "mpif.h"

    private 

    public :: mpi_error_handler_init

contains

    subroutine traceback_err_handler(comm, err_code)
        integer, intent(in) :: comm, err_code
        integer :: ierr, rank
        character(len=12) :: rank_str

        call MPI_Comm_rank(MPI_COMM_WORLD, rank, ierr)
        write (rank_str, '(i12)') rank

        call tracebackqq('MPI traceback error handler called by rank: '//rank_str)
        call MPI_Abort(comm, err_code, ierr)

    end subroutine traceback_err_handler

    subroutine mpi_err_handler_init

        integer :: ierr
        integer :: traceback_handler

        call MPI_Comm_create_errhandler(traceback_err_handler, traceback_handler, ierr)
        call MPI_Comm_set_errhandler(MPI_COMM_WORLD, traceback_handler, ierr)

    end subroutine mpi_err_handler_init

end module mpi_error_handler

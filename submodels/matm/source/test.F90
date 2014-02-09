
module test

use calendar, only : get_runtime, date
use error_handler, only : assert

implicit none

private
public run_tests

contains

subroutine test_calendar()
    
    type(date) :: start_date, end_date
    integer :: runtime

    start_date%year = 1
    start_date%month = 1
    start_date%day = 1

    end_date%year = 1
    end_date%month = 1
    end_date%day = 2

    call get_runtime(start_date, end_date, runtime)
    call assert(runtime == 86400, "test_calendar() failed.")
    
end subroutine

subroutine run_tests()

    call test_calendar()

end subroutine

end module



module test

use calendar, only : calendar_timediff, date_type
use error_handler, only : assert

implicit none

private
public run_tests

contains

subroutine test_calendar()
    
    type(date_type) :: start_date, end_date
    integer :: timediff

    start_date%year = 1
    start_date%month = 1
    start_date%day = 1

    end_date%year = 1
    end_date%month = 1
    end_date%day = 2

    call calendar_timediff(start_date, end_date, timediff)
    call assert(timediff == 86400, "test_calendar() failed.")
    
end subroutine

subroutine run_tests()

    call test_calendar()

end subroutine

end module


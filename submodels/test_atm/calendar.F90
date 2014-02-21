
module calendar

use error_handler, only : assert

implicit none

private
public calendar_timediff, calendar_make_date, SECONDS_PER_YEAR

type date
    integer :: year, month, day
end type

integer, parameter :: SECONDS_PER_YEAR = 31536000, SECONDS_PER_DAY = 86400
integer, dimension(12), parameter :: DAYS_PER_MONTH = (/ 30, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 /) 

contains 

! Add a single day to start_date, return date.
subroutine add_day_to_date(start_date, new_date)

    type(date), intent(in) :: start_date
    type(date), intent(out) :: new_date

    new_date = start_date

    if (new_date%day == DAYS_PER_MONTH(new_date%month)) then
        if (new_date%month == 12) then
            new_date%year = new_date%year + 1
            new_date%month = 1
        else
            new_date%month = new_date%month + 1
        endif
        new_date%day = 1
    else
        new_date%day = new_date%day + 1
    endif
    
end subroutine

! Calculate the runtime in seconds based on a start and end date. 
subroutine calendar_timediff(start_date, end_date, runtime)

    ! Index 1 = year, 2 = month, 3 = day.
    type(date), intent(in) :: start_date, end_date
    integer, intent(out) :: runtime

    type(date) :: tmp_date, new_date

    runtime = 0

    ! Ensure that start_date is before end_date
    call assert(start_date%year <= end_date%year, "Start year is not <= end year.")
    if (start_date%year == end_date%year) then 
        if (start_date%month == end_date%month) then
            call assert(start_date%day < end_date%day, "Start year and month are the same, start day < end day.")
        else
            call assert(start_date%month < end_date%month, "Start year is the same, start month > end month.")
        endif
    endif

    ! Just count the days between the two dates.
    tmp_date = start_date
    do while (.true.)
        if (new_date%year == end_date%year .and. &
            new_date%month == end_date%month .and. &
            new_date%day == end_date%day) then
            exit
        endif

        call add_day_to_date(tmp_date, new_date)
        runtime = runtime + SECONDS_PER_DAY

        tmp_date = new_date
    enddo

end subroutine

subroutine calendar_make_date(date_array, date)

    integer, intent(in), dimension(3) :: date_array
    type(date), intent(out) :: date

    date%year = date_array(1)
    date%month = date_array(2)
    date%day = date_array(3)

end subroutine

end module


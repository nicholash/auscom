
module map

use error_handler, only : assert

implicit none

private
public map_type, map_element_type

integer, parameter :: MAX_KEY_LEN = 256, MAX_ENTRIES = 100

type map_element_type
    character(len=256) :: file_name
    character(len=256) :: var_name
end type

type map_type
    type(map_element_type), dimension(MAX_ENTRIES) :: val
    character(len=MAX_KEY_LEN), dimension(MAX_ENTRIES) :: key
    logical, dimension(MAX_ENTRIES) :: in_use
contains
    procedure :: init => map_init
    procedure :: put => map_put
    procedure :: get => map_get
end type

contains

subroutine map_init(tbl)

    class(map_type), intent(inout) :: tbl

    integer :: i

    do i=1, MAX_ENTRIES
        tbl%key(i) = ''
        tbl%in_use(i) = .false.
    enddo

end subroutine

subroutine map_put(tbl, key, val)

    class(map_type), intent(inout) :: tbl
    character(len=*), intent(in) :: key
    type(map_element_type), intent(in) :: val

    integer :: i
    logical :: done

    done = .false.
    do i=1, MAX_ENTRIES
        if (.not. tbl%in_use(i)) then
            tbl%in_use(i) = .true.
            tbl%key(i) = key
            tbl%val(i) = val
            done = .true.
            exit
        endif
    enddo

    call assert(done, 'Error in map_put(): could not add element')

end subroutine

subroutine map_get(tbl, key, val, found)

    class(map_type), intent(inout) :: tbl
    character(len=*), intent(in) :: key
    type(map_element_type), intent(inout) :: val
    logical, intent(out) :: found

    integer :: i

    found = .false.
    do i=1, MAX_ENTRIES
        if (trim(tbl%key(i)) == trim(key)) then
            val = tbl%val(i)
            found = .true.
            exit
        endif
    enddo

end subroutine

end module


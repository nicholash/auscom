
module data_loader

! Load the coupling field arrays with data from the CORE2 dataset. 

use netcdf
use calendar, only : date
use coupler, only : couple_field_type

implicit none

private
public init_data_loader, load_data

contains 

subroutine load_data(curr_time, coupling_fields)

   
end subroutine

end module


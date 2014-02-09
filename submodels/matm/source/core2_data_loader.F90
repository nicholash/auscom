
module core2_data_loader

! Load the coupling field arrays with data from the CORE2 dataset. 

use netcdf
use calendar, only : date

implicit none

private
public init_data_loader, load_data

contains 

subroutine init_data_loader(coupling_fields)

    type(couple_fields_type), intent(in) :: coupling_fields

    integer :: i

    ! FIXME: Some kind of config file for this?
    do i=1, size(coupling_fields)
        select case(coupling_fields%name)
            case('tair')
                coupling_fields%file_name = 'INPUT/t_10.0001.nc'
                coupling_fields%file_var_name = 'T_10_MOD'
            case('qair')
                coupling_fields%file_name = 'INPUT/q_10.0001.nc'
                coupling_fields%file_var_name = 'Q_10_MOD'
            case('swfld')
                coupling_fields%file_name = 'INPUT/ncar_rad.0001.nc'
                coupling_fields%file_var_name = 'SWDN_MOD'
            case('lwfld')
                coupling_fields%file_name = 'INPUT/ncar_rad.0001.nc'
                coupling_fields%file_var_name = 'LWDN_MOD'
            case('uwnd')
                coupling_fields%file_name = 'INPUT/u_10.0001.nc'
                coupling_fields%file_var_name = 'U_10_MOD'
            case('vwnd')
                coupling_fields%file_name = 'INPUT/v_10.0001.nc'
                coupling_fields%file_var_name = 'V_10_MOD'
            case('rain')
                coupling_fields%file_name = 'INPUT/ncar_precip.0001.nc'
                coupling_fields%file_var_name = 'RAIN'
            case('snow')
                coupling_fields%file_name = 'INPUT/ncar_precip.0001.nc'
                coupling_fields%file_var_name = 'SNOW'
            case('press')
                coupling_fields%file_name = 'INPUT/slp.0001.nc'
                coupling_fields%file_var_name = 'SLP'
            case('runof')
                coupling_fields%file_name = 'INPUT/mean_runof.0001.nc'
                coupling_fields%file_var_name = 'RUNOF'
        end select

    enddo

end subroutine

subroutine load_data(curr_time, coupling_fields)

    integer, intent(in) :: curr_time 
    type(couple_fields_type), intent(in) :: coupling_fields

    
   
end subroutine

end module


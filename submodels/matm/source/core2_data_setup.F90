
module core2_loader

use coupler, only : couple_field_type

implicit none

private
public loader_init, loader_load

subroutine loader_init(coupling_fields)

    type(couple_field_type), dimension(:), intent(inout) :: coupling_fields

    integer :: i

    ! FIXME: check that coupling_fields input has been allocated/initialised.

    ! Create a mapping between coupling variables and input fields.
    ! FIXME: Some kind of config file for this?
    do i=1, size(coupling_fields)
        select case(coupling_fields(i)%name)
            case('tair')
                coupling_fields(i)%file_name = 'INPUT/t_10.0001.nc'
                coupling_fields(i)%file_var_name = 'T_10_MOD'
            case('qair')
                coupling_fields(i)%file_name = 'INPUT/q_10.0001.nc'
                coupling_fields(i)%file_var_name = 'Q_10_MOD'
            case('swfld')
                coupling_fields(i)%file_name = 'INPUT/ncar_rad.0001.nc'
                coupling_fields(i)%file_var_name = 'SWDN_MOD'
            case('lwfld')
                coupling_fields(i)%file_name = 'INPUT/ncar_rad.0001.nc'
                coupling_fields(i)%file_var_name = 'LWDN_MOD'
            case('uwnd')
                coupling_fields(i)%file_name = 'INPUT/u_10.0001.nc'
                coupling_fields(i)%file_var_name = 'U_10_MOD'
            case('vwnd')
                coupling_fields(i)%file_name = 'INPUT/v_10.0001.nc'
                coupling_fields(i)%file_var_name = 'V_10_MOD'
            case('rain')
                coupling_fields(i)%file_name = 'INPUT/ncar_precip.0001.nc'
                coupling_fields(i)%file_var_name = 'RAIN'
            case('snow')
                coupling_fields(i)%file_name = 'INPUT/ncar_precip.0001.nc'
                coupling_fields(i)%file_var_name = 'SNOW'
            case('press')
                coupling_fields(i)%file_name = 'INPUT/slp.0001.nc'
                coupling_fields(i)%file_var_name = 'SLP'
            case('runof')
                coupling_fields(i)%file_name = 'INPUT/mean_runof.0001.nc'
                coupling_fields(i)%file_var_name = 'RUNOF'
        end select

    enddo

end subroutine

subroutine loader_load()
end subroutine

end module

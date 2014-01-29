
module save_field_mod

    use netcdf
    implicit none

    private 

    type save_type
        integer :: count
        integer :: ncid
        integer :: varid
        character(len=256) :: field_name
    end type save_type

    ! Array containing list of field names and associated data, e.g. ncid.
    integer, parameter :: MAX_FIELDS = 256
    type (save_type), dimension(MAX_FIELDS) :: field_meta_data
    integer :: field_num = 1

    public field_write_2d, field_close

    contains  

    subroutine field_setup_2d(field_name, proc_num, nx, ny)
        
        character(len=*), intent(in) :: field_name, proc_num
        integer, intent(in) :: nx, ny
        integer :: ncid, varid, x_dimid, y_dimid, t_dimid

        ! Open a file, set up a meta-data needed to save the field. 
        call check(nf90_create(field_name//'.'//proc_num//'.nc', NF90_CLOBBER, ncid))
        call check(nf90_def_dim(ncid, 'x', nx, x_dimid))
        call check(nf90_def_dim(ncid, 'y', ny, y_dimid))
        call check(nf90_def_dim(ncid, 't', NF90_UNLIMITED, t_dimid))
        call check(nf90_def_var(ncid, field_name, NF90_REAL, (/ x_dimid, y_dimid, t_dimid /), varid))
        call check(nf90_enddef(ncid))

        field_meta_data(field_num)%field_name = field_name
        field_meta_data(field_num)%ncid = ncid 
        field_meta_data(field_num)%varid = varid
        field_meta_data(field_num)%count = 1

        field_num = field_num + 1
        if (field_num > MAX_FIELDS) then
            stop 'save_file_mod::file_setup()'
        end if

    end subroutine

    subroutine field_write_2d(field_name, proc_num, field_data)
        ! Search through field names and find appropriate file handle.
        ! Save to file. 

        character(len=*), intent(in) :: field_name, proc_num
        real, dimension(:,:), intent(in) :: field_data

        integer :: start(3), count(3)
        integer :: idx
        logical :: found
        found = .false.

        call get_field_index(field_name, idx, found)
        if (.not. found) then
            call field_setup_2d(field_name, proc_num, size(field_data, 1), size(field_data, 2))
        end if

        call get_field_index(field_name, idx, found)
        if (.not. found) then
            stop 'save_field_mod::field_write'
        end if

        count = (/ size(field_data, 1), size(field_data, 2), 1 /)
        start = (/ 1, 1, field_meta_data(idx)%count /)
        field_meta_data(idx)%count = field_meta_data(idx)%count + 1 

        ! Write 
        call check(nf90_put_var(field_meta_data(idx)%ncid, field_meta_data(idx)%varid, field_data, start=start, count=count))
        call check(nf90_sync(field_meta_data(idx)%ncid))

    end subroutine

    subroutine field_close(field_name)

        character(len=*), intent(in) :: field_name

        integer :: idx
        logical :: found

        call get_field_index(field_name, idx, found)
        if (.not. found) then
            stop 'save_field_mod::field_close()'
        end if

        call check(nf90_close(field_meta_data(idx)%ncid))
        
    end subroutine

    subroutine get_field_index(field_name, idx, found)

        character(len=*), intent(in) :: field_name
        integer, intent(out) :: idx
        logical, intent(out) :: found

        found = .false.
        do idx=1, field_num
            if (field_name == field_meta_data(idx)%field_name) then
                found = .true.
                return 
            end if
        end do
       
    end subroutine get_field_index

    subroutine check(status)
        integer, intent ( in) :: status
        
        if(status /= nf90_noerr) then 
          print *, trim(nf90_strerror(status))
          stop 'save_field_mod::check()'
        end if
    end subroutine check  

end module save_field_mod


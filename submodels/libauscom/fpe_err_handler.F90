
module fpe_err_handler

    use ifcore
    use ifport

    implicit none
    private 

    public :: fpe_err_handler_init

contains

    subroutine traceback_err_handler(signal, code)
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

    end subroutine traceback_err_handler

    subroutine fpe_err_handler_init

        integer :: ret

        ret = ieee_handler('set', 'overflow', traceback_err_handler)
        ret = ieee_handler('set', 'division', traceback_err_handler)
        ret = ieee_handler('set', 'invalid', traceback_err_handler)

    end subroutine fpe_err_handler_init

end module fpe_err_handler

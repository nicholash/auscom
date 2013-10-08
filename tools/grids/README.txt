
- "The corners of a cell cannot be defined modulo 360 degrees. For example, a cell located over Greenwich will have to be defined with corners at -1.0 deg and 1.0 deg but not with corners at 359.0 deg and 1.0 deg" OASIS user guide p35

- Seems there is a bug in the ACCESS-OM OASIS grids. The nt62 corners grid breaks the above rule. The UM grid looks OK.

- The order of operations is as follows:
    1) make oasis grids based on old oasis grids and new ocean.
    2) make the new CICE grid based on new ocean.
    3) use the above method to make the existing CICE grid from the existing ocean. This is a test.
    3) regrid CICE inputs based on old and new CICE grids. 

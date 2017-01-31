# Job types
    - Diagnostic
    - PrimaryDiagnostic
    - AMWGDiagnostic
    - Publish
    - Model
    - Ncclimo
    - Transfer


# Transfer
    inputs: 
        globus username (string)
        globus password (string)
        source endpoint UUID (string)
        source username (string)
        source password (string)
        source path (string)
        destination endpoint UUID (string)
        destination username (string)
        destination password (string)
        destination path (string)
    outputs:
        success/failure (int)
        status (num completed/total) (string stream)

# Diagnostic
    inputs:
        obspath (string)
        modelpath (string)
        sets (string)
        package (string)
        outputdir (string)
        colormap (string)
        vars (string)
    outputs:
        obs, model, diff files for each variable, placed in the output directory (directory)
        log files (directory)

# PrimaryDiagnostic
    inputs:
    projectdir
        mpas_meshfile
        mpas_remapfile
        pop_remapfile
        remap_files_dir
        GPCP_regrid_wgt_file
        CERES_EBAF_regrid_wgt_file
        ERS_regrid_wgt_file
        test_native_res
        yr_offset
        ref_case
        ref_case_dir
        test_native_res
        obs_ocndir
        obs_seaicedir
        obs_sstdir
        obs_iceareaNH
        obs_iceareaSH
        obs_icevolNH
    outputs:
        plots, saved to the projectdir

# Publish
    inputs:
        optional: Transfer job (move to server)
        target_directory (string), the directory to be published
        publication_name (string), the name to give the publication
        organization (string), the organization name
        firstname (string), the first name of the person publishing
        lastname (string), the last name
        description (string), a description of the publication
        datanode (string), the datanode (default pcmdi11.llnl.gov)
        facets (list of strings),
    outputs:
        success/failure

# Climo
    inputs:
    outputs:

# Model
    inputs:
        machine,
        code base,
        compset,
        resolution,
        namelists,
        length of simulation,
        desired output
    outputs:

# Time series
    inputs:
    outputs:

# CMOR
    inputs:
    outputs:

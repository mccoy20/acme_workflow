# acme_workflow
A workflow tool for the ACME project

# Installation

First install the workflow 
    git clone https://github.com/sterlingbaldwin/acme_workflow.git
    cd acme_workflow
    conda env create -f acme.yml
    source activate acme

Then install the globus online client
    https://github.com/globusonline/transfer-api-client-python
    cd transfer-api-client-python
    python setup.py install

# Usage

    usage: workflow.py [-h] [-c CONFIG] [-d] [-s STATE]

    optional arguments:
    -h, --help            show this help message and exit
    -c CONFIG, --config CONFIG
                            Path to configuration file
    -d, --debug           Run in debug mode
    -s STATE, --state STATE
                            Path to a json state file


An example json configuration file is supplied in the repo, and follows the following template.
All fields can be specified in the config file, or if left out (for example passwords), they will be prompted for at run time.

    {
        # A path to the output directory, each set of years will be nested below this in a folder named year_set_NUMBER
        "output_path": "/space2/sbaldwin/output",

        # A path to where to cache the data
        "data_cache_path": "/space2/sbaldwin/cache",

        # The hostname of where the model data will be generated
        "compute_host": "edison.nersc.gov",

        # Your username on the compute system
        "compute_username": "",

        # Your password on the compute system 
        "compute_password": "",

        # The hostname of the machine doing the post processing (the machine running the workflow script)
        "processing_host": "aims4.llnl.gov",

        # Credentials for that machine
        "processing_username": "",
        "processing_password": "",

        # Globus credentials
        "globus_username": "",
        "globus_password": "",

        # Globus UUIDs for the source (compute host) and the destination (post processing machine)
        # These can be found by going to (the globus app)[globus.org/app/transfer], selecting "Endpoints" and browsing to desired endpoint
        # The following are source=edison and destination=aims4
        "source_endpoint": "b9d02196-6d04-11e5-ba46-22000b92c6ec",
        "destination_endpoint": "43d64772-a82e-11e5-99d3-22000b96db58",

        # The path to where on the compute machine the data will be located
        "source_path": "/global/homes/s/sbaldwin/test",

        # A regular expression for matching the output files
        # If this is changed, there are several places in the code where offsets will need to be changed,
        #   specifically the filename_to_file_list_key and filename_to_year_set functions
        "output_pattern": "\\.cam\\.h0\\.[0-9][0-9][0-9][0-9]-[0-9][0-9]\\.nc",

        # The start year of the simulation
        "simulation_start_year": 1,

        # The end year of the simulation
        "simulation_end_year": 10,

        # The frequency in years to compute climotologies and run diagnostics
        "set_frequency": 5,

        # The caseId to use for the experiment
        "experiment": "20161117.beta0.A_WCYCL1850S.ne30_oEC_ICG.edison",

        # Credentials for the diagnostic viewer
        "diag_viewer_username": "btest",
        "diag_viewer_password": "test",
        "diag_viewer_server": "http://pcmdi10.llnl.gov:8008",

        # The path to the observation set used for diagnostics
        "obs_for_diagnostics_path": "/export/baldwin32/data/obs_for_diagnostics/",

        # The path to the regrid map used in generating climos, a copy should be included in the repo
        "regrid_map_path": "/export/baldwin32/projects/acme_workflow/resources/map_ne30np4_to_fv129x256_aave.20150901.nc",

        # The type of batch system that this will be run under. Allowed values are 'slurm', 'pbs', or 'none'
        "batch_system_type": "slurm"
    }
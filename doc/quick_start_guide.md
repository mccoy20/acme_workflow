# Super Quick Start Guide

Use this guide if you're already an acme1 or aims4 user.

For a new run all you will need is to setup your runs configuration file. Make a copy of the sample config file
```
wget https://raw.githubusercontent.com/sterlingbaldwin/acme_workflow/master/run.cfg
```


Once you have the file, open it in your favorite editor. There are are 12 values that must be changed before you're ready to run. You can find an explanation of each of them [here](setup_guide.md)

The keys you need to change before running the first time are:
```
[global]
output_path = /p/cscratch/acme/<YOUR_USERNAME>/output
data_cache_path = /p/cscratch/acme/<YOUR_USERNAME>/input
simulation_end_year = SOMENUMBER
set_frequency = [LIST, OF, NUMBERS]
run_id = YOUR_RUN_ID

[transfer]
source_path = PATH_TO_REMOTE_DATA
source_endpoint = A_GLOBUS_ENDPOINT_ID
destination_endpoint = A_GLOBUS_ENDPOINT_ID
```

* For each run, the contents of output_path will be overwritten.
* This configuration setup assumes you want to run all the diagnostics, including the coupled_diags. If you're interested in an atmosphere only run, there are two changes to make. 

```
[global]
...
output_patterns = {"STREAMS":"streams", "ATM":"cam.h0", "MPAS_AM": "mpaso.hist.am.timeSeriesStatsMonthly", "MPAS_CICE": "mpascice.hist.am.timeSeriesStatsMonthly", "MPAS_RST": "mpaso.rst.0", "MPAS_O_IN": "mpas-o_in", "MPAS_CICE_IN": "mpas-cice_in"}
...
set_jobs = ["ncclimo", "timeseries", "amwg", "coupled_diag"]
```

For ATM only runs change these to:

```
[global]
...
output_patterns = {"ATM":"cam.h0"}
...
set_jobs = ["ncclimo", "timeseries", "amwg"]
```




#### output_path
This is the local path to store processed output

#### data_cache_path
This is the local path to store unprocessed model data

#### simulation_end_year
The highest year number to expect

#### set_frequency
A list of lengths of processing sets. E.g set_frequency = [5, 10] will run the processing jobs for every 5 years, and every 10 years. If run on 10 years of data, it will create 3 job sets, 1-5, 6-10, 1-10

#### run_id
An arbitrary identifyer for each post processing run. This should be updated for each run or it will over write the html output of previous runs.

#### source_path
The path on the source_endpoint to look for model output.

#### source_endpoint
A globus endpoind UUID, the default is edison.nersc.gov

#### destination_endpoint
The globus endpoint UUID for the machine doing the post-processing. The default is acme1.llnl.gov.

### Running

Running on acme1 and aims4 is very easy. Simply activate the conda environment provided, and run the script.
```
source activate /p/cscratch/acme/bin/acme
python /p/cscratch/acme/bin/acme_workflow/workflow.py -c /path/to/your/run.cfg
```

In interactive mode, if the terminal is closed or you log out, it will stop the process (but the runs managed by SLURM will continue). See below for headless mode instructions.

    python workflow.py -c run.cfg

![initial run](http://imgur.com/ZGuJUCk.png)

Once globus has transfered the first year_set of data, it will start running the post processing jobs.

![run in progress](http://imgur.com/URU4OVY.png)


### headless mode
Uninterupted run in headless mode that wont stop if you close the terminal, writing to a custom log location, with no cleanup after completion
```
nohup python /p/cscratch/acme/bin/acme_workflow/workflow.py -c ./run.cfg --no-ui &
```

This run can continue after you close the termincal and log off the computer. While running in headless mode, you can check run_state.txt for the run status. This file can be found in your output directory.

```
less /p/cscratch/acme/<YOUR_USERNAME>/output/run_state.txt
```

![run_state](http://imgur.com/zS8f57g.png)

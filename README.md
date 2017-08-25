# UK Census Data API

[![Build Status](https://travis-ci.org/virgesmith/UKCensusAPI.png?branch=master)](https://travis-ci.org/virgesmith/UKCensusAPI) [![License](https://img.shields.io/github/license/mashape/apistatus.svg)](https://opensource.org/licenses/MIT)

This package provides both a `python` and an `R` wrapper around the nomisweb census data API, enabling:

- querying table metadata
- autogenerating customised python and R query code for future use
- automated cached data downloads
- modifying the geography of queries
- adding descriptive information to tables (from metadata)

The code is primarily written in python, but we also supply an R interface (using the `reticulate` package) for convenience.

## Prerequisites

### Software

- python3, pip, numpy and pandas
- R version 3.3.3 or higher (if using the R interface)

### API key

It is recommended that you register with [nomisweb](https://www.nomisweb.co.uk) before using this package and use the API key the supply you in all queries. Without a key, queries may be truncated.

Once registered, you will find your API key on [this page](https://www.nomisweb.co.uk/myaccount/webservice.asp). You should not divulge this key to others.

The key should be defined in an environment variable, like so:
```
user@host:~$ echo $NOMIS_API_KEY
0x0000000000000000000000000000000000000000
```
R users can use the standard practice of storing the key in their `.Renviron` file: R will set the environment on startup, which will be visible to python.

This avoids hard-coding the API key into code, which could easily end up in a publically accessible repo.

Queries can be customised on geographical coverage, geographical resolution, and table fields, the latter can be filtered to include only the category values you require.

Since census data is essentially static, it makes little sense to download the data every time it is requested: all data downloads are cached.

## Installation

### python (from github)
```
user@host:~$ pip install git+https://github.com/virgesmith/UKCensusAPI.git
``` 
### python (from cloned repo):
```
user@host:~/dev/UKCensusAPI$ ./setup.py install
``` 
and to test
```
user@host:~/dev/UKCensusAPI$ ./setup.py test
``` 
### R
```
> devtools::install_github("virgesmith/UKCensusAPI")
```

## Usage

### Interactive Query

The first thing users may want to do is an interactive query. All you need to do is specify the name of a census table. The script will then iterate over the categories within the table, prompting you user to select the categories and values you're interested in.

Once done you'll be prompted to (optionally) specify a geography for the data - a geographical region and a resolution.

Finally, if you've specified the geography, the script will ask if you want to download (and cache) the data immediately.

The script then produces the following files:

- a json file containing the table metadata
- python and R code snippets that build the query and call this package to download the data 
- (optionally, depending on above selections) the data itself (which is cached)

These files are all saved in the cache directory (default is `/tmp/UKCensusAPI`).

The code snippets are designed to be copy/pasted into user code. The (cached) data and metadata can simply be loaded by user code as required.

Note for R users - there is no direct R script for the interactive query largely due to the fact it will not work from within RStudio (due to the way RStudio handles stdin).

### Data reuse

Existing cached data is always used in preference to downloading. The data is stored locally using a filename based on the table name and md5 hash of the query used to download the data. This way, different queries on the same table can be stored.

To force the data to be downloaded, just delete the cached data. 

### Query Reuse

The code snippets can simply be inserted into user code, and the metadata (json) can be used as a guide for modifying the query, either manually or automatically.

### Switching Geography

Existing queries can easily be modified to switch to a different geographical area and/or a different geographical resolution. 

This allows, for example, users to write models where the geographical coverage and resolution can be user inputs.

Examples of how to do this are in [`geoquery.py`](examples/geoquery.py) and [`geoquery.R`](examples/geoquery.R).

## Code

- [`Nomisweb.py`](ukcensusapi/Nomisweb.py) - python class containing the core API functionality.
- [`NomiswebApi.R`](R/NomiswebApi.R) - R wrapper for the above above python class.
- [`Query.py`](ukcensusapi/Query.py) - python class containing the query functionality
- [`Package.R`](R/Package.R) - R code that initialises the python module
- [`interactive.py`](inst/scripts/interactive.py) - interactive python script for building queries and downloading data for later use
- [`geoquery.py`](inst/examples/geoquery.py) - example code illustrating how the geography of an existing query can be easily modified
- [`geoquery.R`](inst/examples/geoquery.R) - R version of the above

Queries have three distinct subtypes:

- metadata: query a table for the fields and categories it contains
- geography: retrieve a list of area codes of a particular type within a given region of another (larger) type.
- data: retrieve data from a table using a query built from the metadata and geography.

Data is cached locally to avoid unnecessary requests to nomisweb.co.uk.

Using the interactive query builder, and a known table, you can select geography, categories and category values. The code will assemble the query, then download and cache the data.

The query builder also prints python code that can be subsequently used in a non-interactive application that requires the data.

### Public methods (python)

TODO link to python function documentation...

### Public functions (R)

See the man pages, which can be accessed from RStudio using the command `?UKCensusAPI`
TODO make this actually work


### Interactive Query Builder

This functionality requires that you already know the name of the census table of interest, and want to define a custom query on that table, for a specific geography at a specific resolution.

If you're unsure about which table to query, Nomisweb provide a useful [table finder](https://www.nomisweb.co.uk/census/2011/data_finder). NB Not all census tables are available at all geographical resolutions, but the above link will enumerate the available resolutions for each table.


## Interactive Query Example

Run the script. You'll be prompted to enter the name of the census table of interest:

<pre>
az@AzLaptop ~/dev/UKCensusAPI $ inst/scripts/interactive.py 
Cache directory:  /tmp/UKCensusAPI/
Cacheing local authority codes
Nomisweb census data interactive query builder
See README.md for details on how to use this package
Census table: <b>KS401EW</b>
</pre>

The table description is displayed. The script then interates through the available fields.
```
KS401EW - Dwellings, household spaces and accommodation type
```
You are now prompted to select the categories you require. For the purposes of this example let's say we only want a subset of the fields. Required values should be comma separated, or where contiguous, separated by '...'.

<pre>
CELL:
  0 (All categories: Dwelling type)
  1 (Unshared dwelling)
  2 (Shared dwelling: Two household spaces)
  3 (Shared dwelling: Three or more household spaces)
  4 (All categories: Household spaces)
  5 (Household spaces with at least one usual resident)
  6 (Household spaces with no usual residents)
  7 (Whole house or bungalow: Detached)
  8 (Whole house or bungalow: Semi-detached)
  9 (Whole house or bungalow: Terraced (including end-terrace))
  10 (Flat, maisonette or apartment: Purpose-built block of flats or tenement)
  11 (Flat, maisonette or apartment: Part of a converted or shared house (including bed-sits))
  12 (Flat, maisonette or apartment: In a commercial building)
  13 (Caravan or other mobile or temporary structure)
Select categories (default 0): <b>7...13</b>
</pre>
Select the output type you want (absolute values or percentages)
<pre>
MEASURES:
  20100 (value)
  20301 (percent)
Select categories (default 0): <b>20100</b>
</pre>
For the purposes of this example we don't require the RURAL_URBAN field in our output, so we just hit return to accept the default selection. When the default is selected, the query builder will prompt you for whether you want to include this field in the output. (If something other than the default is not selected, the query builder will always assume that you want the field in the output.)
<pre>
RURAL_URBAN:
  0 (Total)
  1 (Urban city and town in a sparse setting)
  2 (Urban major conurbation)
  3 (Urban minor conurbation)
  4 (Urban city and town)
  101 (Rural (total))
  6 (Rural village in a sparse setting)
  7 (Rural hamlet and isolated dwellings in a sparse setting)
  8 (Rural town and fringe)
  9 (Rural village)
  10 (Rural hamlet and isolated dwellings)
  100 (Urban (total))
  5 (Rural town and fringe in a sparse setting)
Select categories (default 0): <b>&#8629;</b>
include in output? (y/n) <b>n</b>
</pre>
Now you can optionally select the geographical area(s) you want to cover. This can be a single local authority, multiple local authorities, England, England & Wales, GB or UK.
<pre>
Add geography? (y/N): <b>y</b>

Geographical coverage
E/EW/GB/UK or LA name(s), comma separated: <b>Leeds</b>
</pre>
Now select the geographical resolution required. Currently supports local authority, MSOA, LSOA, and OA:
<pre>
Resolution (LA/MSOA/LSOA/OA): <b>MSOA</b>
</pre>
You will then be prompted to choose whether to download the data immediately. If so, the query builder assembles the query and computes an md5 hash of it. It then checks the cache directory if a file with this name exists and will load the data from the file if so. If not, the query builder downloads the data and save the data in the cache directory. 

```
Getting data...
Writing metadata to  /tmp/UKCensusAPI/KS401EW_metadata.json
Downloading and cacheing data: /tmp/UKCensusAPI/KS401EW_2d17ead209999cbc7a1e7f5a299ccba5.tsv
Writing metadata to  /tmp/UKCensusAPI/KS401EW_metadata.json

Writing python code snippet to /tmp/UKCensusAPI/KS401EW.py

Writing R code snippet to /tmp/UKCensusAPI/KS401EW.R
user@host:~$
```
Regardless of whether you selected geography, or downloaded the data, the query builder will generate python and R code snippets for later use.

The generated python code snippet is:

```
"""
KS401EW - Dwellings, household spaces and accommodation type

Code autogenerated by UKCensusAPI
(https://github.com/virgesmith/UKCensusAPI)
"""

# This code requires an API key, see the README.md for details

# Query url:
# https://www.nomisweb.co.uk/api/v01/dataset/NM_618_1.data.tsv?CELL=7...13&MEASURES=20100&RURAL_URBAN=0&date=latest&geography=1245714681...1245714688&select=GEOGRAPHY_CODE%2CCELL%2COBS_VALUE

import ukcensusapi.Nomisweb as CensusApi

api = CensusApi.Nomisweb("/tmp/UKCensusAPI/")
table = "KS401EW"
table_internal = "NM_618_1"
query_params = {}
query_params["RURAL_URBAN"] = "0"
query_params["select"] = "GEOGRAPHY_CODE,CELL,OBS_VALUE"
query_params["date"] = "latest"
query_params["geography"] = "1245714681...1245714688"
query_params["MEASURES"] = "20100"
query_params["CELL"] = "7...13"
KS401EW = api.get_data(table, table_internal, query_params)
```
The the R code:
```
# KS401EW - Dwellings, household spaces and accommodation type

# Code autogenerated by UKCensusAPI
#https://github.com/virgesmith/UKCensusAPI

# This code requires an API key, see the README.md for details
# Query url: https://www.nomisweb.co.uk/api/v01/dataset/NM_618_1.data.tsv?CELL=7...13&MEASURES=20100&RURAL_URBAN=0&date=latest&geography=1245714681...1245714688&select=GEOGRAPHY_CODE%2CCELL%2COBS_VALUE

library("UKCensusAPI")
cacheDir = "/tmp/UKCensusAPI/"
api = UKCensusAPI::instance(cacheDir)
table = "KS401EW"
table_internal = "NM_618_1"
queryParams = list(
  RURAL_URBAN = "0",
  select = "GEOGRAPHY_CODE,CELL,OBS_VALUE",
  date = "latest",
  geography = "1245714681...1245714688",
  MEASURES = "20100",
  CELL = "7...13"
)
KS401EW = UKCensusAPI::getData(api, table, table_internal, queryParams)
```
Users can then copy and paste the generated code snippets into their models, modifying as necessary, to automate the download of the correct data. The metadata looks like this:

```
{
  "description": "KS401EW - Dwellings, household spaces and accommodation type",
  "fields": {
    "RURAL_URBAN": {
      "0": "Total",
      "1": "Urban city and town in a sparse setting",
      "2": "Urban major conurbation",
      "3": "Urban minor conurbation",
      "4": "Urban city and town",
      "101": "Rural (total)",
      "6": "Rural village in a sparse setting",
      "7": "Rural hamlet and isolated dwellings in a sparse setting",
      "8": "Rural town and fringe",
      "9": "Rural village",
      "10": "Rural hamlet and isolated dwellings",
      "100": "Urban (total)",
      "5": "Rural town and fringe in a sparse setting"
    },
    "FREQ": {
      "A": "Annually"
    },
    "GEOGRAPHY": {
      "2092957699": "England",
      "2092957700": "Wales",
      "2092957703": "England and Wales"
    },
    "MEASURES": {
      "20100": "value",
      "20301": "percent"
    },
    "CELL": {
      "0": "All categories: Dwelling type",
      "1": "Unshared dwelling",
      "2": "Shared dwelling: Two household spaces",
      "3": "Shared dwelling: Three or more household spaces",
      "4": "All categories: Household spaces",
      "5": "Household spaces with at least one usual resident",
      "6": "Household spaces with no usual residents",
      "7": "Whole house or bungalow: Detached",
      "8": "Whole house or bungalow: Semi-detached",
      "9": "Whole house or bungalow: Terraced (including end-terrace)",
      "10": "Flat, maisonette or apartment: Purpose-built block of flats or tenement",
      "11": "Flat, maisonette or apartment: Part of a converted or shared house (including bed-sits)",
      "12": "Flat, maisonette or apartment: In a commercial building",
      "13": "Caravan or other mobile or temporary structure"
    }
  },
  "nomis_table": "NM_618_1"
}
```



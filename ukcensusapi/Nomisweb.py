
import os
import json
import hashlib
from collections import OrderedDict
from urllib import request
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.parse import urlencode
from socket import timeout
import pandas as pd
#import numpy as np


# The core functionality for accessing the www.nomisweb.co.uk API
class Nomisweb:

  # static constants
  URL = "https://www.nomisweb.co.uk/"
  KEY = os.environ.get("NOMIS_API_KEY")

  # timeout for http requests
  Timeout = 15

  # Define Nomisweb geographic area codes
  LAD = 464 # defined in NM_144_1 (also 463 is county not district and returns fewer entries)
  # https://www.nomisweb.co.uk/api/v01/dataset/NM_144_1/geography/2092957703TYPE464.def.sdmx.json
  MSOA = 297
  LSOA = 298
  OA = 299

  # Country-level area codes
  England = 2092957699
  EnglandWales = 2092957703
  GB = 2092957698
  UK = 2092957697

  # initialise, supplying a location to cache downloads
  def __init__(self, cache_dir):
    self.cache_dir = cache_dir
    # ensure cache_dir is interpreted as a directory
    if not self.cache_dir.endswith("/"):
      self.cache_dir += "/"
    if not os.path.exists(self.cache_dir):
      os.mkdir(self.cache_dir)
      # TODO check dir created
    if Nomisweb.KEY is None:
      print("Warning - no API key found, downloads may be truncated.\n"
            "Set the KEY value in the environment variable NOMIS_API_KEY.\n"
            "Register at www.nomisweb.co.uk to obtain a key")

    print("Cache directory: ", self.cache_dir)
    print("Cacheing local authority codes")

    # TODO how best to deal with site unavailable...
    try:
      response = request.urlopen(self.URL, timeout=Nomisweb.Timeout)
    except (HTTPError, URLError, timeout) as error:
      print('ERROR: ', error, ' accessing', self.URL)

    # static member
    Nomisweb.cached_lad_codes = self.__cache_lad_codes()
    
  def get_geo_codes(self, la_codes, code_type):

    # force input to be a list
    if not isinstance(la_codes, list):
      la_codes = [la_codes]

    geo_codes = []
    for i in range(0, len(la_codes)):
      path = "api/v01/dataset/NM_144_1/geography/" + str(la_codes[i]) + "TYPE" \
           + str(code_type) + ".def.sdmx.json?"
      rawdata = self.__fetch_json(path, {})

      # use try-catch block to deal with any issues arising from the returned json
      # which are likely due to invalid/empty LA codes
      try:  
        n_results = len(rawdata["structure"]["codelists"]["codelist"][0]["code"])
        # seems a bit daft not to take advantage of the fact we know the length
        for j in range(0, n_results):
          geo_codes.append(rawdata["structure"]["codelists"]["codelist"][0]["code"][j]["value"])
      except (KeyError, ValueError):
        print(la_codes[i], " does not appear to be a valid LA code")
    return self.__shorten(geo_codes)

  def get_lad_codes(self, la_names):
    if not isinstance(la_names, list):
      la_names = [la_names]
    codes = []
    for la_name in la_names:
      if la_name in Nomisweb.cached_lad_codes:
        codes.append(Nomisweb.cached_lad_codes[la_name])
    return codes

  def get_url(self, table_internal, query_params):

    # python dicts have nondeterministic order, see
    # https://stackoverflow.com/questions/14956313/why-is-dictionary-ordering-non-deterministic
    # this is problematic for the cacheing, so we insert alphabetically into an OrderedDict
    # (which preserves insertion order)
    ordered = OrderedDict()
    for key in sorted(query_params):
      ordered[key] = query_params[key]

    return Nomisweb.URL + "api/v01/dataset/" + table_internal + ".data.tsv?" + str(urlencode(ordered))

  # r_compat forces function to return strings (either cached filename, or error msg)
  # Two reasons for this:
  # - pandas/R dataframes conversion is done via matrix (which drops col names)
  # - reporting errors to R is useful (print statements aren't displayed in R(Studio))
  def get_data(self, table, table_internal, query_params, r_compat = False):
    query_params["uid"] = Nomisweb.KEY
    query_string = self.get_url(table_internal, query_params)

    filename = self.cache_dir + table + "_" + hashlib.md5(query_string.encode()).hexdigest()+".tsv"

    # retrieve if not in cache
    if not os.path.isfile(filename):
      meta = self.get_metadata(table)
      self.write_metadata(table, meta)
      print("Downloading and cacheing data: " + filename)
      request.urlretrieve(query_string, filename) #, timeout = Nomisweb.Timeout)

      # check for empty file, if so delete it and report error
      if os.stat(filename).st_size == 0:
        os.remove(filename)
        errormsg = "ERROR: Query returned no data. Check table and query parameters"
        if r_compat:
          return errormsg
        else:
          print(errormsg)
          return
    else:
      print("Using cached data: " + filename)

    # now load from cache and return
    if r_compat:
      return filename
    else:
      return pd.read_csv(filename, delimiter='\t')

  def get_metadata(self, table_name):
    path = "api/v01/dataset/def.sdmx.json?"
    query_params = {"search": "*"+table_name+"*"}

    data = self.__fetch_json(path, query_params)

    # return empty if no useful metadata returned (likely table doesnt exist)
    if not data["structure"]["keyfamilies"]:
      return

    # this is the nomis internal table name
    table = data["structure"]["keyfamilies"]["keyfamily"][0]["id"]

    rawfields = data["structure"]["keyfamilies"]["keyfamily"][0]["components"]["dimension"]
    fields = {}
    for rawfield in rawfields:
      field = rawfield["conceptref"]
      fields[field] = {}
      # further query to get categories
      path = "api/v01/dataset/"+table+"/"+field+".def.sdmx.json?"
      #print(path)

      try:
        fdata = self.__fetch_json(path, {})
      except timeout:
        print("HTTP timeout requesting metadata for " + table_name)
        return {}
      except (HTTPError, URLError):
        print("HTTP error requesting metadata for " + table_name)
        return {}
      else:
        values = fdata["structure"]["codelists"]["codelist"][0]["code"]
        #print(field+":")
        for value in values:
          # KEYs are stored as strings for json compatibility
          fields[field][value["value"]] = value["description"]["value"]

    result = {"nomis_table": table,
              "description": data["structure"]["keyfamilies"]["keyfamily"][0]["name"]["value"],
              "fields": fields}

    return result

  # loads metadata from cached json if available, otherwises downloads from nomisweb.
  # NB category KEYs need to be converted from string to integer for this data to work properly, see convert_code
  def load_metadata(self, table_name):
    filename = self.cache_dir + table_name + "_metadata.json"
    # if file not there, get from nomisweb
    if not os.path.isfile(filename):
      print(filename, " not found, downloading...")
      return self.get_metadata(table_name)
    else:
      with open(filename) as metafile:
        meta = json.load(metafile)

    return meta

# private

  # download and cache the nomis codes for local authorities
  def __cache_lad_codes(self):

    data = self.__fetch_json("api/v01/dataset/NM_144_1/geography/" \
         + str(Nomisweb.EnglandWales) + "TYPE" + str(Nomisweb.LAD) + ".def.sdmx.json?", {})
    if data == {}:
      return []
    rawfields = data["structure"]["codelists"]["codelist"][0]["code"]

    codes = {}
    for rawfield in rawfields:
      codes[rawfield["description"]["value"]] = rawfield["value"]
    return codes

  # given a list of integer codes, generates a string using the nomisweb shortened form
  # (consecutive numbers represented by a range, non-consecutive are comma separated
  def __shorten(self, code_list):

    # empty evals to False
    if not code_list:
      return ""
    if len(code_list) == 1:
      return str(code_list[0])

    code_list.sort() # assume this is a modifying operation
    short_string = ""
    index0 = 0
    index1 = 0 # appease lint
    for index1 in range(1, len(code_list)):
      if code_list[index1] != (code_list[index1-1] + 1):
        if index0 == index1:
          short_string += str(code_list[index0]) + ","
        else:
          short_string += str(code_list[index0]) + "..." + str(code_list[index1-1]) + ","
        index0 = index1
    if index0 == index1:
      short_string += str(code_list[index0])
    else:
      short_string += str(code_list[index0]) + "..." + str(code_list[index1])
    return short_string

  def __fetch_json(self, path, query_params):
    # add API KEY to params
    query_params["uid"] = Nomisweb.KEY

    query_string = Nomisweb.URL + path + str(urlencode(query_params))

    #print(query_string)
    reply = {}
    try:
      response = request.urlopen(query_string, timeout=Nomisweb.Timeout)
    except (HTTPError, URLError) as error:
      print('ERROR: ', error, '\n', query_string)
    except timeout:
      print('ERROR: request timed out\n', query_string)
    else:
      reply = json.loads(response.read().decode("utf-8"))
    return reply

  # save metadata as JSON for future reference
  def write_metadata(self, table, meta):

    filename = self.cache_dir + table + "_metadata.json" 
    print("Writing metadata to ", filename)
    with open(filename, "w") as metafile:
      json.dump(meta, metafile, indent=2)

  # append <column> numeric values with the string values from the metadata
  # NB the "numeric" values are stored as strings in both the table and the metadata
  # this doesnt need to be a member
  def convert_code(self, table, column, metadata):

    if not column in metadata["fields"]:
      print(column, " is not in metadata")
      return
    if not column in table.columns:
      print(column, " is not in table")
      return

    # convert KEYs on the fly to integers (if they've been loaded from json they will be strings)
    lookup = {int(k):v for k, v in metadata["fields"][column].items()}
    table[column + "_NAME"] = table[column].map(lookup)

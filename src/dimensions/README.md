# Reporting Yearly BU Research Output with Dimensions

Get a list of research publications written by those with a list of given last names

## Background

- We get a _yearly request_ from the department of 'Professional Development & Postdoctoral Affairs'
  to report on the publishing behavior of our post-docs (provided as a list of names).
- This was previously handled (last year) by [@tomhohenstein](https://github.com/tomhohenstein),
  but seeing as we have the [Dimensions](dimensions.ai) service and API, we could build
  something more robust
- Dimensions provides a powerful database of publications with metadata regarding publishing
  institution and funding not found in other databases
- They provide a page of their site where you can run custom queries on their data backend at:
  [https://app.dimensions.ai/dsl](https://app.dimensions.ai/dsl).

## What We're Filtering On

_NOTE: Assumptions in these queries are time-dependent, and won't work on queries for many years ago._

### Reserachers Query

Acquire additional data about BU researchers with last names from our csv.

|criteria|explanation|
|:-------|:----------|
|`where last_name in [...]`|match the last names from the provided csv list|
|`current_research_org in [...]`|make sure they're affiliated with BU|
|`last_publication_year`|make sure they've published in the years since|
|`first_publication_year`|we don't expect someone currently in their postdoc to have been publishing for a decade already|
|`researchers[all] limit 1000`| get all the info we can (for debugging) and as many as we can at a time|
|`skip 0`|for if we have to page through results (`total_count`>1000). if so, switch to `1000`|

### Publications Query

|criteria|explanation|
|:-------|:----------|
|`where researchers.id in ["rid_512", "rid_513", ..., "rid_1023"]`|matches our researchers from the first step|
|`year in [YEAR_START:YEAR_END]`|check that it was published in our range|
|publications[id+...+researchers]|get a bunch of stuff, but not everything or it takes forever|
|`limit 1000 skip 0`| same as above|

## Usage

You'll have to run the program multiple times with various parts of the 'main' function commented out.

All we're really doing is:
- constructing queries based on input
- manually running those queries in the browser
- collecting the main data from what's returned into json files
- extracting some additional data from those json files
- reporting on that data and creating exports

```$ python ./dimensions.py```

_NOTE: This workflow has a mix of manual and automated steps. It does NOT make calls to the [Dimensions API](https://app.dimensions.ai/dsl)_

### General Steps

---
I - **Get list of researchers** from Dimensions and store as `researchers.json`

- ensure delivery of a csv file with the list of desired names of the researchers with only their last name in the first column

- update the values in the 

- run `getListOfResearchObjectsFromDimensionsAPI` with the csv involved to produce `output/researcher_queries.txt`
```getListOfResearchObjectsFromDimensionsAPI(researchers_csv_filename)```

- copy/paste the query/queries into the text area at [https://app.dimensions.ai/dsl](https://app.dimensions.ai/dsl) and 'Run'
- 'Copy to clipboard' the returned results, compiling the `researchers:[]` (potentially across queries) into a new file
  `data/researchers.json` file constituting a list of json objects: `[ {}, {}, ..., {} ]`

_NOTE: pay close attention to the `_stats.total_count` value of the return object from the API! if this number is over 1000,
  you'll have to page through your results by adding the `skip` variable to your query (see `queries.txt`)_

- process the `data/researchers.json` file and output `rids.json`, while creating `output/researchers.tsv`.
```getListOfResearcherIDsFromDimensionsObjects()```

---
II - **Get matching publications** from Dimensions API

- use the list of researcher ids (from the previous step) to construct a new set of queries against the dimensions API,
  and outputting them into `output/publications_queries.txt`.
```getListOfPublicationObjectsFromDimensionsResearcherIDs(researcher_ids)```

_NOTE: the list of researcher_ids will almost definitely be above the maximum number of items Dimensions will allow in a query (`LIMIT_FOR_IN_FILTER`).
  this makes us have to cut the `researcher_id` list into parts and run them as multiple queries and manually combine the
  results afterward_

- run this set of queries by the same method as before, collecting the publication objects into a `data/publications.json` file
  of a similar format (`[{},{},{}]`)
  
- process through this list of publications eliminating duplicates and preparing an `output/publications.tsv`.
```deduplicateListOfPublications(ls_bu_researcher_ids)```

---

III - **Gather Statistics** about what we've determined

- Check the output against what we'd expect in order to debug and troubleshoot (see below)

```text
$ python dimensions.py

NUMBER OF PUBLICATIONS published (2018 - 2018): 723


-- statistics --
average number of publications per researcher: (723/500) = 1.446 : GOOD
percentage of researchers who published: (370/500) = 74.0 : GOOD
most number of articles published by a single researcher: 20
number of researchers who published more than the maximum 8 papers expected (per-year): 35

-- NOTE: check output/ for additional files --
```

- **Verify**: Double-check that the first two measures are listed as "GOOD" (or at least aren't _too_ bad) and the
  number of researchers who published more than X isn't _too_ ridiculous
- **Report**: Provide additional statistics that might also be of interest

### Problems Running the Scripts

1. Check that you have all the relevant files and filenames in the set up correctly/as expected
2. Make sure that all of your `.json` files are valid using [jsonlint.com](https://jsonlint.com)
3. Try running the methods one at a time in the order above.
4. Make sure you're manually updating the `data/*.json` lists by re-running the queries to Dimensions. the script
   reads these `data/` files, not the direct Dimensions results.
5. Check with Dimensions support if the API (syntax, functionality) changes in a way that breaks it
6. Contact Aidan Sawyer (atla5), including your `data/` and `output/` files in the email.

### Troubleshooting and Verifying Results

|id  |stat|expectation|
|:---|:---|:----------|
| A  |ratio of publications to researchers| 1.1 <= `avg_num_...` <= 1.9|
| B  |% of researchers who published >=1 publication| 50 <= `apx_percentage_...` <= 90|
| C  |researchers with high number of publications| 8? /shrug |

- **Skewed Ratio (A)**: is significantly `HIGH` or `LOW`: the overall ratio/health is in question and you should review your data inputs/method 
- **Skewed Distribution (B)**: : the distribution of publications/activity level is weird and we might want to check that the researchers are the right level
- **Abnormally Productive Researchers (C)**: there were researchers who published more than we'd expect them to, so we'll want to manually check `output/researcher_to_check.tsv`|

  1. take a closer look at that researcher by asking Dimensions about them with the query below
  2. make sure that their information fits what you'd expect for a postdoc (and that they're not a professor/PI) 
  3. see if there's an entry in the original csv that includes their `first_name`
  4. if needed, manually filter these researcher_ids out, by removing them from the CSV, or just the query in step 2 

```search researchers where id in ["PROBLEM_RID_1", "PROBLEM_RID_2", ..., "PROBLEM_RID_N"] return researchers[all] limit 1000```

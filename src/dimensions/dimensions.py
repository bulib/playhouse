import json
from os.path import dirname, realpath, join

# get the list of researchers: https://app.dimensions.ai/dsl
id_BU = 'grid.189504.1'
id_BU_ACADEMY = 'grid.448566.d'
id_BU_MEDICAL = 'grid.475010.7'
LAST_NAMES_LIST = ["ADHIKARI,","AGOP NERSESIAN,","AGRAHARI,","AHN,","AKINTEWE,", "...","ZOU,","ZUBERER,"]
yr_start = 2017
yr_end = 2018
q_GET_LIST_OF_RESEARCH_IDS = """\n\n\n
  /* -- QUERY TO GET THE LIST OF RESEARCHERS -- */
  search researchers  
    where last_name in {}
    and current_research_org.id in {}
    and last_publication_year in {}
  return researchers[all] limit 1000 skip 0\n\n\n
  """.format(
    str(LAST_NAMES_LIST).replace("'","\""), 
    "[{},{},{}]".format(id_BU,id_BU_ACADEMY,id_BU_MEDICAL), 
    "{}:{}".format(yr_start,yr_end)
  )
print(q_GET_LIST_OF_RESEARCH_IDS)

# translate list of researcher objects into list of ids
researcher_id_list = []
directoryPath = dirname(realpath(__file__))
with open(join(directoryPath,"2018_researchers.json"), "r") as researchers_json:
  research_list = json.load(researchers_json)
  initial_count = len(research_list)

  for researcher in research_list:
    researcher_id_list.append(researcher["id"])

    if "obsolete" in researcher and researcher["redirect"]:
      for id in researcher["redirect"]:
        researcher_id_list.append(id)

researcher_id_list = list(set(researcher_id_list)) # deduplicate
print("number of researchers: " + str(len(research_list)))
print("number of researcher_ids: " + str(len(researcher_id_list)))
print(researcher_id_list)


# use the list of 'researcher_id's to query dimensions for publications
q_GET_LIST_OF_PUBLICATIONS = """\n\n\n
  /* -- QUERY TO GET THE LIST OF PUBLICATIONS -- */
  search publications
    where researchers.id in {}
    and year in {}
  return publications[title+year+doi+issn+publisher+date+times_cited+type+researchers] limit 1000 skip 0\n\n\n
  """.format(
    str(researcher_id_list).replace("'","\""), 
    "[{}:{}]".format(yr_start, yr_end)
  )
print(q_GET_LIST_OF_PUBLICATIONS)
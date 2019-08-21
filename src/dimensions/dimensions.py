import json, math
from os.path import dirname, realpath, join


LIMIT_FOR_IN_FILTER = 512

directoryPath = dirname(realpath(__file__))
yr_start = 2018
yr_end = 2018
yr_current = 2019


# get the list of researchers: https://app.dimensions.ai/dsl
def getListOfResearchObjectsFromDimensionsAPI():
  id_BU = 'grid.189504.1'
  id_BU_ACADEMY = 'grid.448566.d'
  id_BU_MEDICAL = 'grid.475010.7'
  LAST_NAMES_LIST = ["ADHIKARI,","AGOP NERSESIAN,","AGRAHARI,","AHN,","AKINTEWE,", "...","ZOU,","ZUBERER,"]
  q_GET_LIST_OF_RESEARCH_IDS = """\n\n\n
    /* -- QUERY TO GET THE LIST OF RESEARCHERS -- */
    search researchers  
      where last_name in {}
      and current_research_org.id in {}
      and last_publication_year in {}
    return researchers[all] limit 1000 skip 0\n\n\n
    """.format(
      str(LAST_NAMES_LIST).replace("'","\""), 
      '["{}","{}","{}"]'.format(id_BU,id_BU_ACADEMY,id_BU_MEDICAL), 
      "[{}:{}]".format(yr_start,yr_current)
    )
  print(q_GET_LIST_OF_RESEARCH_IDS)

# translate list of researcher objects into list of ids
def getListOfResearcherIDsFromDimensionsObjects():
  researcher_id_list = []
  with open(join(directoryPath,"2018_researchers.json"), "r") as researchers_json:
    research_list = json.load(researchers_json)

    for researcher in research_list:
      researcher_id_list.append(researcher["id"])

      if "obsolete" in researcher and researcher["redirect"]:
        for id in researcher["redirect"]:
          researcher_id_list.append(id)

  researcher_id_list = list(set(researcher_id_list)) # deduplicate
  print("number of researchers: " + str(len(research_list)))
  print("number of researcher_ids: " + str(len(researcher_id_list)))
  # print(researcher_id_list)
  return researcher_id_list


def chunckListIntoListOfListsBasedOnLimit(original_list, limit):
  """
    dimensions API has limits on how long each list can be, 
    this breaks larger lists into multiple lists for chained calls
  """
  len_old_list = len(original_list)
  len_new_list = math.ceil(len(original_list) / limit)
  new_list = []
  for i in range(len_new_list):
    start_index = i*limit   # e.g. (0 -> 0, 1->512, 2->1024)
    end_index = ((i+1)*limit)-1 # e.g. (0 -> 511, 1->1023)
    print("{}[{}] => [{}:{}]".format(len_old_list, i, start_index, end_index))
    new_list.append(original_list[start_index:end_index]) # e.g. 0 -> 0:511, 1 -> 512:1023, 2-> 1024:1535
  return new_list


def getListOfPublicationObjectsFromDimensionsResearcherIDs(researcher_ids):

  list_of_lists = chunckListIntoListOfListsBasedOnLimit(researcher_ids, LIMIT_FOR_IN_FILTER)
  num_queries = len(list_of_lists)

  # use the list of 'researcher_id's to query dimensions for publications
  for i in range(num_queries):
    q_GET_LIST_OF_PUBLICATIONS = """\n\n\n
      /* -- QUERY TO GET THE LIST OF PUBLICATIONS  ({} of {}) -- */
      search publications
        where researchers.id in {}
        and year in {}
      return publications[title+year+doi+issn+publisher+date+times_cited+type] limit 1000 skip 0\n\n\n
      """.format(
        i+1, num_queries,
        str(list_of_lists[i]).replace("'","\""), 
        "[{}:{}]".format(yr_start, yr_end)
      )
    print(q_GET_LIST_OF_PUBLICATIONS)

def deduplicateListOfPublications():
  with open(join(directoryPath,"2018_publications.json"), "r") as publications_json:
    ls_publication_ids = []
    publication_list = json.load(publications_json)
    initial_list_size = len(publication_list)

    for publication in publication_list:
      pub_id = publication["doi"] if "doi" in publication else publication["issn"][0]
      if(pub_id not in ls_publication_ids):
        ls_publication_ids.append(pub_id)

    print("{} -> {}".format(str(initial_list_size), str(len(ls_publication_ids))))
      

# print out query to dimensions API and manually process it into *researchers.json
getListOfResearchObjectsFromDimensionsAPI()

# process researchers.json into list of researcherIds 
ls_researcher_ids = getListOfResearcherIDsFromDimensionsObjects()

# print out query to dimensions API, then manually process it into publications.json  
getListOfPublicationObjectsFromDimensionsResearcherIDs(ls_researcher_ids)

# process the '*publications.json' 
deduplicateListOfPublications()

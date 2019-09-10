import json, math, re
from os.path import dirname, realpath, join

# programmatic variables from/for the Dimensions API or for the script
LIMIT_FOR_IN_FILTER = 512  # can't check against more than this many items in a given list in one query (e.g. 'where researchers.id in [...]')
directoryPath = dirname(realpath(__file__))  # the directory we're running the script in

# direct inputs into the query
yr_start = 2018
yr_end = 2018
yr_current = 2019

# sensible parameters we're using to sanity-check and filter the results
low_estimate_of_avg_number_of_publications_per_researcher = 0.8
high_estimate_of_avg_number_of_publications_per_researcher = 2.5
high_estimate_of_publications_wed_expect_a_single_postdoc_to_publish_in_a_year = 6
greatest_number_of_years_ago_wed_expect_a_postdoc_to_publish_a_paper = 8

# assorted stats to be filled as the program runs
approximate_num_researchers = 0
approximate_num_researchers_that_published = 0

# get the list of researchers: https://app.dimensions.ai/dsl
def getListOfResearchObjectsFromDimensionsAPI():
  id_BU = 'grid.189504.1'
  id_BU_ACADEMY = 'grid.448566.d'
  id_BU_MEDICAL = 'grid.475010.7'
  LAST_NAMES_LIST = ["ADHIKARI,","AGOP NERSESIAN,","AGRAHARI,","AHN,","AKINTEWE,", "...","ZOU,","ZUBERER,"]
  
  earliest_sensible_publication_year_for_a_postdoc = yr_start - greatest_number_of_years_ago_wed_expect_a_postdoc_to_publish_a_paper
  q_GET_LIST_OF_RESEARCH_IDS = """\n\n\n
    /* -- QUERY TO GET THE LIST OF RESEARCHERS -- */
    search researchers  
      where last_name in {}
      and current_research_org.id in {}
      and last_publication_year in {}
      and first_publication_year in {}
    return researchers[all] limit 1000 skip 0\n\n\n
    """.format(
      str(LAST_NAMES_LIST).replace("'","\""), 
      '["{}","{}","{}"]'.format(id_BU,id_BU_ACADEMY,id_BU_MEDICAL), 
      "[{}:{}]".format(yr_start,yr_current),
      list(range(earliest_sensible_publication_year_for_a_postdoc, yr_end+1))  # any of the years spanning between those years
    )
  print(q_GET_LIST_OF_RESEARCH_IDS)

# translate list of researcher objects into list of ids
def getListOfResearcherIDsFromDimensionsObjects():
  researcher_id_list = []
  researcher_entry_list = []
  with open(join(directoryPath,"2018_researchers.json"), "r") as researchers_json:
    research_list = json.load(researchers_json)

    for researcher in research_list:
      rid = researcher["id"]
      last_name = researcher["last_name"]
      first_name = researcher["first_name"]

      researcher_id_list.append(rid)
      researcher_entry_list.append("{}\t{}\t{}\n".format(last_name, rid, first_name))

      if "obsolete" in researcher and researcher["redirect"]:
        for id in researcher["redirect"]:
          if id in researcher_id_list:
            continue
          researcher_id_list.append(id)
          researcher_entry_list.append("{}\t{}\t{}\n".format(last_name, id, first_name))

  print("number of researchers: " + str(len(research_list)))
  print("number of researcher_ids: " + str(len(researcher_id_list)))

  with open(join(directoryPath,"2018_researchers.tsv"), "w") as researchers_tsv: 
    researchers_tsv.write("last_name\tresearcher id\tfirst_name\n")
    researcher_entry_list.sort()
    for entry in researcher_entry_list:
      researchers_tsv.write(entry)
  
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
      return publications[id+title+year+date+doi+issn+publisher+volume+issue+pages+times_cited+researchers+type] limit 1000 skip 0\n\n\n
      """.format(
        i+1, num_queries,
        str(list_of_lists[i]).replace("'","\""), 
        "[{}:{}]".format(yr_start, yr_end)
      )
    print(q_GET_LIST_OF_PUBLICATIONS)


class Publication:
  def __init__(self, publication, rids):
    self.pid = publication["id"] if "id" in publication else ""
    self.date = publication["date"] if "date" in publication else ""
    self.rids = "||".join(rids)

    raw_title = publication["title"] if "title" in publication else ""
    self.title = re.sub(r"\s+"," ", raw_title) if raw_title else ""
    self.doi = publication["doi"] if "doi" in publication else ""
    self.issn = publication["issn"][0] if "issn" in publication else ""

    self.pub = publication["publisher"] if "publisher" in publication else ""
    self.vol = publication["volume"] if "volume" in publication else ""
    self.iss = publication["issue"] if "issue" in publication else ""
    self.pages = publication["pages"] if "pages" in publication else ""

  def __str__(self):
    return "{}\t{}\t{}\t{}\t{}\t'{}'\t{}\t{}\t{}\t'{}'\n".format(
      self.pid, self.date, self.rids, 
      self.doi, self.issn, 
      self.pub, self.vol, self.iss, self.pages, self.title
    )

def deduplicateListOfPublications(ls_bu_researcher_ids):
  ls_pub_ids = []
  ls_publication_entries = []
  with open(join(directoryPath,"2018_publications.json"), "r") as publications_json:
    publication_list = json.load(publications_json)
    initial_list_size = len(publication_list)

    for publication in publication_list:
      pid = publication["id"]

      rids = []
      include_publication = False
      for researcher in publication["researchers"]:
        rid = researcher["id"]
        if(rid and rid not in rids and rid in ls_bu_researcher_ids):
          rids.append(rid)
      
      if pid not in ls_pub_ids:
        ls_pub_ids.append(pid)
        ls_publication_entries.append(Publication(publication, rids))
    
    print("{} -> {}".format(str(initial_list_size), str(len(ls_publication_entries))))

  # write out new tsv file
  ls_publication_entries.sort(key=lambda p: p.date)
  with open(join(directoryPath,"2018_publications.tsv"), "w") as output_file:
    output_file.write("article_id\tpublication_date\tresearcher_ids\tdoi\tissn\tpublisher\tvolume\tissue\tpages\ttitle\n")
    for pub_obj in ls_publication_entries:
      output_file.write(str(pub_obj))


# print out query to dimensions API and manually process it into *researchers.json
# getListOfResearchObjectsFromDimensionsAPI()

# process researchers.json into list of researcherIds 
ls_researcher_ids = getListOfResearcherIDsFromDimensionsObjects()

# print out query to dimensions API, then manually process it into publications.json  
getListOfPublicationObjectsFromDimensionsResearcherIDs(ls_researcher_ids)

# process the '*publications.json' 
deduplicateListOfPublications(ls_researcher_ids)

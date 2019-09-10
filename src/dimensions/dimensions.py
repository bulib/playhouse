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
high_estimate_of_avg_number_of_publications_per_researcher = 2.0
high_estimate_of_any_number_of_publications_per_researcher = 8
greatest_number_of_years_ago_wed_expect_a_postdoc_to_publish_a_paper = 8

# publication object
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

  @staticmethod
  def headerStr():
    return "article_id\tpublication_date\tresearcher_ids\tdoi\tissn\tpublisher\tvolume\tissue\tpages\ttitle\n"
  def __str__(self):
    return "{}\t{}\t{}\t{}\t{}\t'{}'\t{}\t{}\t{}\t'{}'\n".format(
      self.pid, self.date, self.rids, 
      self.doi, self.issn, 
      self.pub, self.vol, self.iss, self.pages, self.title
    )

# get the list of researchers: https://app.dimensions.ai/dsl
def getListOfResearchObjectsFromDimensionsAPI():
  id_BU = 'grid.189504.1'
  id_BU_ACADEMY = 'grid.448566.d'
  id_BU_MEDICAL = 'grid.475010.7'
  with open(join(directoryPath,"data","2018_postdoc_names.csv"), "r") as names_data:
    ls_names = [re.split(' |,',line)[0] for line in names_data]
    LAST_NAMES_LIST = set(ls_names)
  
  earliest_sensible_publication_year_for_a_postdoc = yr_start - greatest_number_of_years_ago_wed_expect_a_postdoc_to_publish_a_paper
  q_GET_LIST_OF_RESEARCH_IDS = """/* -- QUERY TO GET THE LIST OF RESEARCHERS -- */
search researchers  
  where last_name in {}
  and current_research_org.id in {}
  and last_publication_year in {}
  and first_publication_year in {}
return researchers[all] limit 1000 skip 0\n
""".format(
      str(LAST_NAMES_LIST).replace("'","\"").replace("{","[").replace("}","]"), 
      '["{}","{}","{}"]'.format(id_BU,id_BU_ACADEMY,id_BU_MEDICAL), 
      "[{}:{}]".format(yr_start,yr_current),
      list(range(earliest_sensible_publication_year_for_a_postdoc, yr_end+1))  # any of the years spanning between those years
    )
  with open(join(directoryPath,"output","researcher_queries.txt"), "w") as queries_output:
    queries_output.write(q_GET_LIST_OF_RESEARCH_IDS)

def getListOfResearcherIDsFromRawJSONFileOfThem():
  ls_rids = []
  with open(join(directoryPath,"data","2018_rids.json"), "r") as rids_json:
    for rid in json.load(rids_json):
      ls_rids.append(rid)
  return ls_rids

# translate list of researcher objects into list of ids
def getListOfResearcherIDsFromDimensionsObjects():
  researcher_id_list = []
  researcher_entry_list = []
  with open(join(directoryPath,"data","2018_researchers.json"), "r") as researchers_json:
    research_list = json.load(researchers_json)

    for researcher in research_list:
      # gather data about the researcher, including their researcherID
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
          
          line_to_add = "{}\t{}\t{}\n".format(last_name, id, first_name)
          if line_to_add not in researcher_entry_list:
            researcher_entry_list.append(line_to_add)

  # print("number of researchers: " + str(len(research_list)))
  # print("number of researcher_ids: " + str(len(researcher_id_list)))

  with open(join(directoryPath,"output","2018_researchers.tsv"), "w") as researchers_tsv: 
    researchers_tsv.write("last_name\tresearcher_id\tfirst_name\n")
    researcher_entry_list.sort()
    for entry in researcher_entry_list:
      researchers_tsv.write(entry)
  
  with open(join(directoryPath,"data","2018_rids.json"), "w") as rids_json:
    rids_json.write(str(researcher_id_list).replace("'",'"'))
  return researcher_id_list


def _chunkListIntoListOfListsBasedOnLimit(original_list, limit):
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
    # print("{}[{}] => [{}:{}]".format(len_old_list, i, start_index, end_index))
    new_list.append(original_list[start_index:end_index]) # e.g. 0 -> 0:511, 1 -> 512:1023, 2-> 1024:1535
  return new_list


def getListOfPublicationObjectsFromDimensionsResearcherIDs(researcher_ids):

  list_of_lists = _chunkListIntoListOfListsBasedOnLimit(researcher_ids, LIMIT_FOR_IN_FILTER)
  num_queries = len(list_of_lists)

  # use the list of 'researcher_id's to query dimensions for publications
  for i in range(num_queries):
    q_GET_LIST_OF_PUBLICATIONS = """/* -- QUERY TO GET THE LIST OF PUBLICATIONS  ({} of {}) -- */
search publications
  where researchers.id in {}
  and year in {}
return publications[id+title+year+date+doi+issn+publisher+volume+issue+pages+times_cited+researchers+type] limit 1000 skip 0\n
""".format(
        i+1, num_queries,
        str(list_of_lists[i]).replace("'","\""), 
        "[{}:{}]".format(yr_start, yr_end)
      )
    with open(join(directoryPath,"output","publications_queries.txt"), "a") as queries_output:
      queries_output.write(q_GET_LIST_OF_PUBLICATIONS)


def deduplicateListOfPublications(ls_bu_researcher_ids):
  ls_pub_ids = []
  ls_publication_entries = []
  with open(join(directoryPath,"data","2018_publications.json"), "r") as publications_json:
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
        
    # deduplicate 
    '''
    print("number of publications before and after filtering: {} -> {}".format(
      str(initial_list_size), str(len(ls_publication_entries))
    ))
    '''

  # write out new tsv file
  ls_publication_entries.sort(key=lambda p: p.date)
  with open(join(directoryPath,"output","2018_publications.tsv"), "w") as output_file:
    output_file.write(Publication.headerStr())
    for pub_obj in ls_publication_entries:
      output_file.write(str(pub_obj))
  return ls_publication_entries


def findPublicationOddities(ls_researcher_ids, num_researchers, num_publications):
  # create dictionary for each researcher id to the number of works they've created
  dict_researchers = {}
  with open(join(directoryPath,"output","2018_publications.tsv"), "r") as output:
    for line in output:
      for rid in ls_researcher_ids:
        if(rid in line):
          if rid in dict_researchers.keys():
            dict_researchers[rid] += 1
          else:
            dict_researchers[rid] = 1

  # calculate some statistics about this 
  approximate_number_of_publishing_researchers = len(dict_researchers)  # skewed by researchers with more than one researcher_ids
  researcher_ids_to_check = []
  ls_num_publications_per_individual = []
  highest_actual_number_of_publications_per_grad_student = 0

  with open(join(directoryPath,"output","researchers_to_check.tsv"), 'w') as researchers_to_check:
    researchers_to_check.write("researcher_id\tnum_published")
    for (rid, num_pub) in dict_researchers.items():
      # prepare stats for average publications per individual
      ls_num_publications_per_individual.append(num_pub)

      # flag researchers who we think have published more than we'd expect
      if(num_pub >= high_estimate_of_any_number_of_publications_per_researcher):
        researcher_ids_to_check.append(rid)
        researchers_to_check.write("'{}'\t{}\n".format(rid, str(num_pub)))

      # keep update of the highest number of publications
      if(num_pub >= highest_actual_number_of_publications_per_grad_student):
        highest_actual_number_of_publications_per_grad_student = num_pub

  # calculate and report statistics
  print("\nNUMBER OF PUBLICATIONS published ({} - {}): {}\n\n".format(
    yr_start, yr_end, num_publications
  ))

  print("-- statistics --")
  avg_num_publications_per_researcher = (1.0*num_publications)/num_researchers 
  if avg_num_publications_per_researcher <= low_estimate_of_avg_number_of_publications_per_researcher:
    avg_msg = "LOW"
  elif avg_num_publications_per_researcher >= high_estimate_of_avg_number_of_publications_per_researcher:
    avg_msg = "HIGH"
  else:
    avg_msg = "GOOD"
  print("average number of publications per researcher: ({}/{}) = {} : {}".format(
    str(num_publications), str(num_researchers), str(avg_num_publications_per_researcher), avg_msg
  ))
  print("percentage of researchers who published: ({}/{}) = {}".format(
    str(approximate_number_of_publishing_researchers), str(num_researchers), 
    str((100.0*(approximate_number_of_publishing_researchers)/num_researchers))
  ))
  print("most number of articles published by a single researcher: " + str(highest_actual_number_of_publications_per_grad_student))
  print("number of researchers who published more than the maximum {} papers expected (per-year): {}".format(
    str(high_estimate_of_any_number_of_publications_per_researcher), str(len(researcher_ids_to_check))
  ))

  print("\n-- NOTE: check output/ for additional files --\n")


if __name__ == "__main__":
  # print out query to dimensions API and manually process it into *researchers.json
  getListOfResearchObjectsFromDimensionsAPI()

  # process researchers.json into list of researcherIds 
  ls_researcher_ids = getListOfResearcherIDsFromDimensionsObjects()

  # print out query to dimensions API, then manually process it into publications.json  
  getListOfPublicationObjectsFromDimensionsResearcherIDs(ls_researcher_ids)

  # process the '*publications.json' 
  ls_publication_entries = deduplicateListOfPublications(ls_researcher_ids)

  # run the end results against 
  num_postdocs = 501
  num_publications = len(ls_publication_entries)
  findPublicationOddities(ls_researcher_ids, num_postdocs, num_publications)

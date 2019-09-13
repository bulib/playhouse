import json
from dimensions_helpers import Publication, _chunkListIntoListOfListsBasedOnLimit
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

low_estimate_of_percentage_of_publishing_researchers = 55
high_estimate_of_percentage_of_publishing_researchers = 90

high_estimate_of_any_number_of_publications_per_researcher = 8
greatest_number_of_years_ago_wed_expect_a_postdoc_to_publish_a_paper = 8

# get the list of researchers: https://app.dimensions.ai/dsl
def getListOfResearchObjectsFromDimensionsAPI(researchers_csv_filename):
    id_BU = 'grid.189504.1'
    id_BU_ACADEMY = 'grid.448566.d'
    id_BU_MEDICAL = 'grid.475010.7'
    num_total_researchers = 0
    with open(join(directoryPath, "data", researchers_csv_filename), mode="r", encoding="utf-8-sig") as names_data:
        ls_names = []
        for line in names_data:
            ls_names.append( re.split(' |,', line)[0] )
            num_total_researchers += 1
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
        str(LAST_NAMES_LIST).replace("'", "\"").replace("{", "[").replace("}", "]"),
        '["{}","{}","{}"]'.format(id_BU, id_BU_ACADEMY, id_BU_MEDICAL),
        "[{}:{}]".format(yr_start, yr_current),
        "[{}:{}]".format(earliest_sensible_publication_year_for_a_postdoc, yr_end)  # any of the years spanning between those years
    )
    with open(join(directoryPath, "output", "researcher_queries.txt"), "w") as queries_output:
        queries_output.write(q_GET_LIST_OF_RESEARCH_IDS)

    return num_total_researchers


def getListOfResearcherIDsFromRawJSONFileOfThem():
    ls_rids = []
    with open(join(directoryPath, "data", "{}_rids.json".format(yr_end)), "r") as rids_json:
        for rid in json.load(rids_json):
            ls_rids.append(rid)
    return ls_rids


# translate list of researcher objects into list of ids
def getListOfResearcherIDsFromDimensionsObjects():
    researcher_id_list = []
    researcher_entry_list = []
    with open(join(directoryPath, "data", "{}_researchers.json".format(yr_end)), "r") as researchers_json:
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

    # create an export of the researchers with their last and first names (for verifying rids)
    with open(join(directoryPath, "output", "researchers.tsv"), "w") as researchers_tsv:
        researchers_tsv.write("last_name\tresearcher_id\tfirst_name\n")
        researcher_entry_list.sort()
        for entry in researcher_entry_list:
            researchers_tsv.write(entry)

    # create an exported list of the rids for use in the query
    with open(join(directoryPath, "data", "{}_rids.json".format(yr_end)), "w") as rids_json:
        rids_json.write(str(researcher_id_list).replace("'", '"'))

    return researcher_id_list


def getListOfPublicationObjectsFromDimensionsResearcherIDs(researcher_ids):
    list_of_lists = _chunkListIntoListOfListsBasedOnLimit(researcher_ids, LIMIT_FOR_IN_FILTER)
    num_queries = len(list_of_lists)

    # use the list of 'researcher_id's to query dimensions for publications
    with open(join(directoryPath, "output", "publications_queries.txt"), "w") as queries_output:
        for i in range(num_queries):
            q_GET_LIST_OF_PUBLICATIONS = """/* -- QUERY TO GET THE LIST OF PUBLICATIONS  ({} of {}) -- */
search publications
  where researchers.id in {}
  and year in {}
return publications[id+title+year+date+doi+issn+publisher+volume+issue+pages+times_cited+researchers+type] limit 1000 skip 0\n
""".format(
                i + 1, num_queries,
                str(list_of_lists[i]).replace("'", "\""),
                "[{}:{}]".format(yr_start, yr_end)
            )
            queries_output.write(q_GET_LIST_OF_PUBLICATIONS)


def deduplicateListOfPublications(ls_bu_researcher_ids):
    ls_pub_ids = []
    ls_publication_entries = []
    with open(join(directoryPath, "data", "{}_publications.json".format(yr_end)), "r") as publications_json:
        publication_list = json.load(publications_json)
        initial_list_size = len(publication_list)

        for publication in publication_list:
            pid = publication["id"]

            rids = []
            include_publication = False
            for researcher in publication["researchers"]:
                rid = researcher["id"]
                if (rid and rid not in rids and rid in ls_bu_researcher_ids):
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
    with open(join(directoryPath, "output", "publications.tsv"), "w") as output_file:
        output_file.write(Publication.headerStr())
        for pub_obj in ls_publication_entries:
            output_file.write(str(pub_obj))
    return ls_publication_entries


def rationalizeAndDescribeOutput(ls_researcher_ids, num_researchers, num_publications):
    # create dictionary for each researcher id to the number of works they've created
    dict_researchers = {}
    with open(join(directoryPath, "output", "publications.tsv"), "r") as output:
        for line in output:
            for rid in ls_researcher_ids:
                if (rid in line):
                    if rid in dict_researchers.keys():
                        dict_researchers[rid] += 1
                    else:
                        dict_researchers[rid] = 1

    # calculate some statistics about this
    approximate_number_of_publishing_researchers = len(dict_researchers)  # skewed by researchers with more than one researcher_ids
    researcher_ids_to_check = []
    ls_num_publications_per_individual = []
    highest_actual_number_of_publications_per_grad_student = 0

    with open(join(directoryPath, "output", "researchers_to_check.tsv"), 'w') as researchers_to_check:
        researchers_to_check.write("researcher_id\tnum_published\n")
        for (rid, num_pub) in dict_researchers.items():
            # prepare stats for average publications per individual
            ls_num_publications_per_individual.append(num_pub)

            # flag researchers who we think have published more than we'd expect
            if num_pub >= high_estimate_of_any_number_of_publications_per_researcher:
                researcher_ids_to_check.append(rid)
                researchers_to_check.write("'{}'\t{}\n".format(rid, str(num_pub)))

            # keep update of the highest number of publications
            if num_pub >= highest_actual_number_of_publications_per_grad_student:
                highest_actual_number_of_publications_per_grad_student = num_pub

    # calculate and report statistics
    print("\nNUMBER OF PUBLICATIONS published ({} - {}): {}\n\n".format(
        yr_start, yr_end, num_publications
    ))

    print("-- statistics --")

    # number of publications per researcher should be between low_estimate_of_avg_num and high_estimate_of_avg_num
    avg_num_publications_per_researcher = (1.0 * num_publications) / num_researchers
    if avg_num_publications_per_researcher <= low_estimate_of_avg_number_of_publications_per_researcher:
        avg_msg = "LOW"
    elif avg_num_publications_per_researcher >= high_estimate_of_avg_number_of_publications_per_researcher:
        avg_msg = "HIGH"
    else:
        avg_msg = "GOOD"
    print("average number of publications per researcher: ({}/{}) = {} : {}".format(
        str(num_publications), str(num_researchers), str(avg_num_publications_per_researcher), avg_msg
    ))

    # we'd expect between approximate_number_of_publishing_researchers to be within a range
    apx_percentage_publishing = (100.0 * approximate_number_of_publishing_researchers) / num_researchers
    if apx_percentage_publishing <= low_estimate_of_percentage_of_publishing_researchers:
        avg_msg = "LOW"
    elif apx_percentage_publishing >= high_estimate_of_percentage_of_publishing_researchers:
        avg_msg = "HIGH"
    else:
        avg_msg = "GOOD"
    print("percentage of researchers who published: ({}/{}) = {} : {}".format(
        str(approximate_number_of_publishing_researchers), str(num_researchers),
        str(apx_percentage_publishing),
        avg_msg
    ))

    # catch professors and others that are associated with more papers than they could effectively author as a postdoc
    print("most number of articles published by a single researcher: " + str(
        highest_actual_number_of_publications_per_grad_student))
    print("number of researchers who published more than the maximum {} papers expected (per-year): {}".format(
        str(high_estimate_of_any_number_of_publications_per_researcher), str(len(researcher_ids_to_check))
    ))

    print("\n-- NOTE: check output/ for additional files --\n")


if __name__ == "__main__":
    # print out query to dimensions API and manually process it into *researchers.json
    num_postdocs = getListOfResearchObjectsFromDimensionsAPI("{}_postdoc_names.csv".format(yr_end))

    # process researchers.json into list of researcherIds
    ls_researcher_ids = getListOfResearcherIDsFromDimensionsObjects()

    # researcher_ids to dis-include (suppose you've identified a few professors from researcher_ids_to_check)
    ls_researcher_ids_to_remove = []
    for rid in ls_researcher_ids_to_remove:
        ls_researcher_ids.remove(rid)

    # print out query to dimensions API, then *manually process* it into publications.json
    getListOfPublicationObjectsFromDimensionsResearcherIDs(ls_researcher_ids)

    # process the '*publications.json'
    ls_publication_entries = deduplicateListOfPublications(ls_researcher_ids)

    # run the end results against
    num_publications = len(ls_publication_entries)
    rationalizeAndDescribeOutput(ls_researcher_ids, num_postdocs, num_publications)

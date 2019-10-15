import math, re

# publication object used to print out the `publiactions.tsv`
class Publication:
    def __init__(self, publication, rids):
        self.pid = publication["id"] if "id" in publication else ""
        self.date = publication["date"] if "date" in publication else ""
        self.rids = "||".join(rids)

        raw_title = publication["title"] if "title" in publication else ""
        self.title = re.sub(r"\s+", " ", raw_title) if raw_title else ""
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



def _chunkListIntoListOfListsBasedOnLimit(original_list, limit):
    """
      dimensions API has limits on how long each list can be,
      this breaks larger lists into multiple lists for chained calls
    """
    len_old_list = len(original_list)
    len_new_list = math.ceil(len(original_list) / limit)
    new_list = []
    for i in range(len_new_list):
        start_index = i * limit  # e.g. (0 -> 0, 1->512, 2->1024)
        end_index = ((i + 1) * limit) - 1  # e.g. (0 -> 511, 1->1023)
        # print("{}[{}] => [{}:{}]".format(len_old_list, i, start_index, end_index))
        new_list.append(original_list[start_index:end_index])  # e.g. 0 -> 0:511, 1 -> 512:1023, 2-> 1024:1535
    return new_list

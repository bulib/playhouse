# playhouse

a collection of experimental/one-off projects conducted by BU Librarians and friends.


_important note: code has been preserved as is, and is not maintained or expected to be completely runnable_

## background

`playhouse` is inhabited by Boston University Librarians and friends interested in
  using python, javascript, php, and other languages to develop simple scripts and
  complex applications to support library work.

this repository contains various projects of interest, often involving consuming
  a number of apis, extracting and enriching data from a given source, and
  using one or more libraries or digital humanities techniques to draw additional
  value or information from it.

these projects are not actively maintained or consumed by the library, but are
  preserved as technical/inspirational examples, proofs of concept, and potential
  placeholders for future development/exploration.

## projects

|filename|project description|
|:-------|:------------------|
|`doi-get-bibtex-from-title.ipynb`|obtain a bibtex record for a given doi (doi.org) after getting its doi from crossref|
|`loc-harverst-modify-newspapers.ipynb`|harvest and modify bibliographic records of digitized newspapers from LoC|
|`loc-visualize-article-sentiment.ipynb`|analyze and visualize polarity data of LoC articles from 'Chronicling America' collection. |
|`nyt-article-congress-api.ipynb`|interact with NYT `articlesearch` and `politics` APIs |
|`nsf-query-boston-awards.ipynb`|interrogate NSF awards API for those given to Boston academics |
|`oclc-find-related-issns.ipynb`|populate list of ISSNs related to given marcxml files, via OCLC xISSN API|
|`osf-find-by-related-orcid.ipynb`|generate a list of records that were created by selected orcid researchers|


## usage

the majority of these projects were generated within/using
  [`jupyter notebooks`](https://jupyter-notebook.readthedocs.io/en/latest/notebook.html),
  which allow python code to be documented/described, run, and displayed in place.


### set-up

`jupyter notebook` is the core requirement for running and interacting with these
  projects. it is included in the greater [`conda`](https://conda.io/docs/index.html)
  package/environment/dependency manager, and can be installed alongside the
  [conda install](https://conda.io/docs/user-guide/install/index.html), or
  [done separately](https://jupyter.readthedocs.io/en/latest/install.html#id4).

### how to run

in order to best view/edit these projects, it's recommended that you run the following
  command in the terminal at the base of this project's directory:

```
$ jupyter notebook /path/to/playhouse/
```

this should take over the command window with 'NotebookApp' logs, opening the
  browser automatically to [http://localhost:8888/tree](http://localhost:8888/tree)
  where you should see an interactive display of the files included in the directory.

to view (and/or edit) a notebook, simply select it from the list and it should
  open in a new tab. see the jupyter docs for [more usage instructions](https://jupyter-notebook.readthedocs.io/en/latest/notebook.html#starting-the-notebook-server).


### advanced: creating an environment

_note: untested legacy docs moved from `install_a_working_python_3.5_environment.md`_

The following instructions will guide you through creating a fresh environment into which to install python 3.5, anaconda, numpy, pandas, matplotlib, and seaborn along with several modules that are commonly used at BU Libraries: pymarc, marcx, textblob, and gensim. The commands below should accomplish that.

This assumes you have installed anaconda.  

```
$ source deactivate
$ conda create --name py3x python=3.5 anaconda numpy pandas matplotlib seaborn
$ source activate py3x

$ pip install https://github.com/edsu/pymarc/archive/python3.zip
$ pip install https://github.com/miku/marcx/archive/master.zip
$ pip install textblob

$ conda install gensim
```

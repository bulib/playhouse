# Google Analytics 

This folder is for hosting our Google Analytics work. 

Please provide some basic information about each notebook that you add. 

### ga-site-review

The ga-site-review.ipynb was created to download daily pageviews for the [data management website](http://www.bu.edu/datamanagement/). It uses [Stijn Debrouwere's Google Analytics Python library](https://github.com/debrouwere/google-analytics/) to simplify the commands. 

The result of the script are csv files for each page with the pageviews from 2013-2015. 

This notebook is part of a set of notebooks for downloading, updating, and visualizing pageview data for Google Analytics. 

### R-plot

This poorly named notebook takes the data generated from the ga-site-review and creats plots using R's ggplot. 

### updater

This notebook updates the pageview data originally downloaded in the ga-site-review. It requires you set the last_update date in cell 2.

When completed the notebook will create a new folder with updated csv files with the new data. The old data is preserved in the "last updated folder."


### update-plotter 

This R notebook uses the data from the updater notebook to create a new set of graphs for each page. The graphs are stored in the same folder as the csv files. 

This notebook also requires that you set the last_update variable, this time in cell 1. 


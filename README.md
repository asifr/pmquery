# Query PubMed and download results to text files

`pmquery.py` searches Pubmed and saves article metadata in JSON-formatted text files. The purpose is to later mine the data. After saving the text files the script creates a zipped archive so things stay compact.

## Requirements

If you don't have the pip utility first install it with:
> easy_install pip

Install all the mandatory dependencies by typing:
> pip install -r requirements.txt

## Usage
Before running the script make sure you edit the config file. The `term` and `ident` parameters indicate the search term and a unique identifier (no spaces allowed), respectively.

To execute the script pmquery uses a Makefile, although executing the python script will produce the same results.

Query the database:

> make query
> python pmquery.py

Delete all data folders, this preserves zipped archives but removes the individual text files:

> make clean

Copyright (c) 2013— Asif Rahman
License: MIT (see LICENSE for details)

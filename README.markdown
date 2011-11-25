Marmir is powerful and fun
==========================

Marmir takes python data structures and turns them into spreadsheets.

It is xlwt and google spreadsheets on steriods.


## Marmir is written with love

He is the organizer of ChiPy (http://chipy.org), one of the top 25 tech in
Chicago (according to Crains Oct 2011), been professionaly developing software
for business for 15 years and he is sick of sub-par Python libraries for
creating business spreadsheets, Brian Ray (@brianray) wrote Marmir.

The name Marmir is 

## Marmir melts in your mouth

Talk about simple to use, wow. Marmir is just this:

``` python

import datetime
import mm

my_data = [ 
    {
        'msg': "My first Cell",
        'id': 1,
        'when': datetime.datetime.now(),
    },
    {
        'msg': "My second Cell",
        'id': 2,
        'when': datetime.datetime.now(),
    },

]

mm_doc = mm.Document(my_data)
mm_doc.write("example.xls")
```


Or you can get fancier:

``` python
import datetime
import mm

my_data = [ 
    {
        'msg': "My first Cell",
        'id': 1,
        'when': mm.Date(datetime.datetime.now(), "%Y-%m-%dT%H:%M:%S%z"),
        'homepage': mm.URL("https://github.com/brianray")
    },
    {
        'msg': "My second Cell",
        'id': 2,
        'when': datetime.datetime.now(),
        'homepage': mm.URL("http://twitter.com/brianray")
    },

]

mm_doc = mm.Document(my_data, "Sheet 1")
mm_doc = mm.Document([1,2,3], "Sheet 2", headers=['count',])
mm_doc.write("example.html")
mm_doc.google_doc_publish("Username", "Pass", "Example Spreadsheet")
```


There is a lot more. Check out the unit tests.



## ... Not in your hand

So the primary goals are:

 * make XLS spreadsheets better than xlwt
 * Create Spreadsheets in Google Docs beter than gdata
 * convert python types automagically, date is a date, int is a int, string is a string, ...
 * do stuff you expect like make columns wider to fit, wrap in some cases
 * make stuff pretty colors and easier to read
 * tools to help generate directy fron Django queries


Some other stuff:

 * do summaries and break out tables
 * add logic and math functions



Copyright
---------

Copyright (c) 2011 Brian Ray


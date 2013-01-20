Marmir is powerful and fun
==========================

Marmir takes Python data structures and turns them into spreadsheets.

It is xlwt and google spreadsheets on steroids.

## Marmir melts in your mouth

Talk about simple to use, wow. Marmir is just this:

``` python

import datetime
import mm

my_data = [ 
    {
        'msg': "My first Row",
        'id': 1,
        'when': datetime.datetime.now(),
    },
    {
        'msg': "My second Row",
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
        'msg': "My first Row",
        'id': 1,
        'when': mm.Date(datetime.datetime.now(), "%Y-%m-%dT%H:%M:%S"),
        'homepage': mm.URL("https://github.com/brianray")
    },
    {
        'msg': "My second Row",
        'id': 2,
        'when': datetime.datetime.now(),
        'homepage': mm.URL("http://twitter.com/brianray", "Tweet Me")
    },

]

mm_doc = mm.Document(my_data)
mm_doc.write("example.html")

# also you can publish to google spreadsheats
mm_doc.write_gdata("Example Spreadsheet", "Username", "Pass")
```

Now for a little Django (https://www.djangoproject.com/) example:

``` python

from yourproject.models import TestModel
from mm.contrib.django.data_model import DjangoDataModel
from mm.contrib.django.grid import DjangoGrid

django_query_set = TestModel.objects.all()
mm_doc = mm.Document(django_query_set, 
              data_model_class=DjangoDataModel, 
              grid_class=DjangoGrid)
mm_doc.write("django_example.xls")
```

There is a lot more. Check out the unit tests.

## ... Not in your hand

So the primary goals are:

 * make XLS spreadsheets better than xlwt
 * Create Spreadsheets in Google Docs
 * convert python types automagically, date is a date, int is a int, string is a string, ...
 * do stuff you expect like make columns wider to fit, wrap in some cases
 * make stuff pretty colors and easier to read
 * generate directy fron Django queries

Some other stuff:

 * do summaries and break out tables
 * add logic and math functions 
 
## Marmir is written with love

Brian Ray [@brianray](http://twitter.com/brianray) wrote Marmir. Brian: is the organizer of ChiPy
(http://chipy.org); one of the top 25 tech in Chicago (according to Crains Oct
2011); been professionaly developing software for business for 15 years ; and
is sick of sub-par Python libraries for creating business spreadsheets.

The name Marmir name from cabining parts of the names Maura and Miranda,
Brian's girls and who this software is deadicated.

Copyright
---------

Copyright (c) 2013 Brian Ray


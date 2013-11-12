Marmir is powerful and fun
==========================

[Marmir](http://brianray.github.com/mm/) takes Python data structures and turns them into spreadsheets.

It is xlwt and google spreadsheets on steroids. 

It also supports: input from Django models; taking Psycopg cursors; writing out ascii tables (like psql does); and will soon support HTML tables as output. The goal is to make it easy to generate many types of useful table files with the least amount of configuration.

## Marmir melts in your mouth

Installing:

```
$ pip install Marmir
```

Talk about simple to use, wow. Marmir is just this:

``` python

import datetime
import mm

now = datetime.datetime.now().replace(microsecond=0)

my_data = [ 
    {
        'msg': "My first Row",
        'id': 1,
        'when': now,
    },
    {
        'msg': "My second Row",
        'id': 2,
        'when': now,
    },

]

mm_doc = mm.Document(my_data)
mm_doc.write("example.xls")
```
Same example above as lists (also node the 'order' argument works in the above as well:
```python
my_headers = ('id', 'msg', 'when')
my_data = (
    (1, "My First Row", now),
    (2, "My Second Row", now)   
)

mm_doc = mm.Document(my_data, order=my_headers)
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
mm_doc.write("example.xls")

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

There is a lot more. Check out the [Examples](https://github.com/brianray/mm/blob/master/EXAMPLES.markdown).

## ... Not in your hand

So the primary goals are:

 * make XLS spreadsheets better than xlwt
 * Create Spreadsheets in Google Docs
 * convert python types automagically, date is a date, int is a int, string is a string, ...
 * do stuff you expect like make columns wider to fit, wrap in some cases
 * make stuff pretty colors and easier to read
 * generate directly from Django queries

Some other stuff:

 * do summaries and break out tables
 * add logic and math functions 
 
## Marmir is written with love

Brian Ray [@brianray](http://twitter.com/brianray) wrote Marmir. Brian: is the organizer of ChiPy
(http://chipy.org); one of Chicago's Top Tech 25 (according to Crains Oct
2011); been professionally developing software for business for 15 years; and
is sick of sub-par Python libraries for creating business spreadsheets.

The name Marmir name from parts of the names Maura and Miranda, the author's girls.


Copyright
---------

Copyright (c) 2013 Brian Ray


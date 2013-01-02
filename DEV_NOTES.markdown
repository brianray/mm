
The basic top level elements are broken up around a Document instance. It is a two step process:

1. Constructing a *Document* with a DataModel and serialzed data via Serializers.
1. Writing of the document.

Pseudo code example:

    # 1. construction
    data = dict | list
    optional: data_model = DataModel(data)
    optional: serializer_class = Serializer(data_model, data) 
    doc = Document( data, data_model, serializer_class, config)
    
    # 2. generation
    doc.write()
    

# 1. Document #

    doc.grid - serializer.serialize() # returns GridBase()

## GridBase population ##

    grid.populate(data) 

grid must have attirbutes: row_count, col_count, headers


grid_data is a 2-D list of data instances of whatever class is found in grid.headers. Every cell has a instance.

For example if grid.headers are:    

    [<class 'mm.model_base.IntFieldType'>, <class 'mm.model_base.StringFieldType'>, <class 'mm.model_base.DateFieldType'>]

In each of these classes they have an attribute 'header_title' assigned to the keys in the data:

    <class 'mm.model_base.IntFieldType'> .header_title = id
    <class 'mm.model_base.StringFieldType'> .header_title = msg
    <class 'mm.model_base.DateFieldType'> .header_title = when

The data looks like this:  

    [{'msg': 'My first Cell', 'when': <class 'mm.model_base.DateFieldType'>, 'id': 1}, {'msg': 'My second Cell', 'homepage':  (<class 'mm.model_base.URLFieldType'>), 'when': datetime.datetime(2013, 1, 1, 11, 12, 50, 194609), 'id': 2}]


So, in the example above the first cell, in the first row (after the headers) is set to 1, the second column in that same row msg is 'My first Cell', and so on.

The 'when' in the first is an actual user defined instance of a DateFieldType.
 


# 2. Writing Documents #

DocumentWriter class provides in which method a document is written: to disk, to a string, or (future) to a remote server or custom protocal.

Composer classes decide the format that the spreadsheet is written. For example, the default, ComposerXLS writes a Excel document (the same format xlwt currently creates). 

Once the data grid is all set, the output is ready to be generated via the composer set to the DocumentWriter. Currently doc.write() or doc.writestr() which handles the data returned by composer.run():

    composer = Composer(data_model, grid, doc)
    composer.run() 


# ComposerBase #

comp.iterate_grid() is available to all Composer classes that inheritae from ComposerBase. It does most of the work. 

write_header() iterates over the field_headers and writes there header_titles. In the above example it would write: 'id', 'msg', 'when'. It calls write_cell but always points at the first row.

It iterates ever row and calls 'start_new_row()' that can be overwritten in the ComposerXLS subclass. 'end_row' is called at the end of every row.

The on each cell, the method 'write_cell' is called passing arguments: row_id, col_id, and the cell data.



## ComposerXLS Internals ##

Wether or not headers are written is dependent on your config you pass in to Document. Otherwise, the default configuration will be used.




# Configuation Settings #


SuppressDebuggerExceptionDialogs=1

























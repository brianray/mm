from document_writers import DocumentWriter
from model_base import DataModel
from config_base import ConfigBase
from serializer_base import Serializer
import logging

log = logging.getLogger(__name__)

class Document(DocumentWriter):
    """
    Document reporesents the abstact view you interact with in order to send
    data for your document and ultimately get output.
    """


    def __init__(self, data, data_model=None, serializer_class=None, config=None):
        """      
         data -- a dict or a list of data you wish to use for a the
                 spreadsheet
         data_model -- (optional) fields defenitions
         serializer_class -- (optional) class to use to serialize raw data
        """
        self.data = data
        self.config = ConfigBase(config)
 
        # make a data model if one does not exist
        if not data_model:
            self.data_model = DataModel(data)

        # Serialize the data       
        # we look at it here once and only once
        # we look at it again when we write
        # goal to pass over data no more than twice, if possible
        if not serializer_class:
            serializer_class = Serializer
        serializer = serializer_class(self.data_model, self.data)

        # returns a grid instance
        self.grid = serializer.serialize()
       
        log.info("Documnet Created")
 
    def set_composer(self, composer):
        self.composer = composer
        





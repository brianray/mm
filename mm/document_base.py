from document_writers import DocumentWriter
from model_base import DataModel
from config_base import ConfigBase
from serializer_base import Serializer
from grid_base import GridBase
import logging

log = logging.getLogger(__name__)

class Document(DocumentWriter):
    """
    Document reporesents the abstact view you interact with in order to send
    data for your document and ultimately get output.
    """


    def __init__(self, 
                    data, 
                    data_model_class=None, 
                    grid_class=None,
                    serializer_class=None, 
                    config=None, 
                    config_dict=None):
        """      
         data -- a dict or a list of data you wish to use for a the
                 spreadsheet
         data_model -- (optional) fields defenitions
         grid_model -- (optional) takes data_model and data and fills grid
         serializer_class -- (optional) class to use to serialize raw data
         config -- (optional) Configuration (ConfigBase) instance
         config_dict -- (optional) a dictionary of key/values of settings
        """
        self.data = data
        self.config = config
        if not self.config:
            self.config = ConfigBase()
        if config_dict:
            self.config.set_dict(config_dict)
 
        # make a data model if one does not exist
        self.data_model_class = data_model_class
        if not data_model_class:
            self.data_model_class = DataModel

        self.data_model = self.data_model_class(data)

        # grid base 
        if not grid_class:
            grid_class = GridBase

        # Serialize the data       
        # we look at it here once and only once
        # we look at it again when we write
        # goal to pass over data no more than twice, if possible
        if not serializer_class:
            serializer_class = Serializer
        serializer = serializer_class(self.data_model, 
                                        self.data,
                                        grid_class=grid_class
                                        )

        # returns a grid instance
        self.grid = serializer.serialize()
       
        log.info("Documnet Created")
 
    def set_composer(self, composer):
        self.composer = composer
        

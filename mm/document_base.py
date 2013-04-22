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
    def __init__(
            self,
            data,
            data_model_class=None,
            grid_class=None,
            serializer_class=None,
            config=None,
            config_dict=None,
            order=None,
            column_types=None):
        """
         data -- a dict or a list of data you wish to use for a the
                 spreadsheet
         data_model -- (optional) fields defenitions
         grid_model -- (optional) takes data_model and data and fills grid
         serializer_class -- (optional) class to use to serialize raw data
         config -- (optional) Configuration (ConfigBase) instance
         config_dict -- (optional) a dictionary of key/values of settings
         order -- (optional) also headers
         column_types -- (optional) a dictionary of column types; e.g. column_name1 is a date column:  {'column_name1': mm.Date)

        """
        self.data = data
        self.config = config
        self.name = None
        self.children = []
        if not self.config:
            self.config = ConfigBase()
        if config_dict:
            self.config.set_dict(config_dict)

        # make a data model if one does not exist
        self.data_model_class = data_model_class
        if not data_model_class:
            self.data_model_class = DataModel

        self.data_model = self.data_model_class(data, order=order, column_types=column_types)

        # grid base
        if not grid_class:
            grid_class = GridBase

        # Serialize the data
        # we look at it here once and only once
        # we look at it again when we write
        # goal to pass over data no more than twice, if possible
        if not serializer_class:
            serializer_class = Serializer
        serializer = serializer_class(
            self.data_model,
            self.data,
            grid_class=grid_class)

        # returns a grid instance
        self.grid = serializer.serialize()

        log.info("Documnet Created")

    def set_composer(self, composer):
        self.composer = composer

    def set_name(self, name):
        self.name = name

    def add_child(self, document):
        self.children.append(document)

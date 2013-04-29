from mm.composer_base import ComposerBase
import logging
log = logging.getLogger(__name__)
pretty_table = False
try:

    import prettytable  # NOQA
    pretty_table = True
except ImportError:
    pass


class ComposerPrettyTable(ComposerBase):

    def write_header(self):
        self.pt.field_names = self.data_model.field_titles

    def row(self, row):
        self.pt.add_row([cell.data for cell in row])

    def run(self, child=None):
        if not pretty_table:
            raise Exception("Module 'prettytable' required for text table output")
        self.pt = prettytable.PrettyTable()
        if self.document.config.headers:
            self.write_header()
        self.iterate_grid()
        self.finish()

        # process any childern
        for doc_child in self.document.children:
            doc_child.writestr(child=self.pt)

        return self.pt

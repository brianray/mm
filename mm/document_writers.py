from composer_xls import ComposerXLS
from mm.contrib.prettytable.composers import ComposerPrettyTable, pretty_table

import os
import tempfile
import logging

log = logging.getLogger(__name__)


class DocumentWriter(object):
    "runs a composer"

    composer_class = None
    composer = None

    def writestr(self, child=False):
        composer_class = self.composer_class
        if not composer_class:
            # default format is XLS
            composer_class = ComposerXLS
            log.info("Setting output format to XLS")
        self.composer = composer_class(self.data_model, self.grid, self)
        return self.composer.run(child=child)

    def write(self, filename):
        ext = os.path.splitext(filename)[-1].lower()
        if ext == "xls":
            self.composer = ComposerXLS(self.data_model, self.grid, self)
            log.info("Setting output format to XLS, based on file extension")
        elif ext == "txt" and pretty_table:
            self.composer = ComposerPrettyTable(self.data_model, self.grid, self)
            log.info("Setting output format to TXT, based on file extension")

        f = open(filename, "w")
        f.write(self.writestr())
        f.close()
        log.info("wrote file: %s" % filename)

    def write_gdata(self, name, username, password, auth_token=None):
        try:
            import gdata
            import gdata.docs.service
        except ImportError:
            raise Exception("Must install package 'gdata' to use write_gdata()")

        tmp_file, tmp_file_path = tempfile.mkstemp()
        self.write(tmp_file_path)

        gd_client = gdata.docs.service.DocsService()
        gd_client.ssl = True
        if not auth_token:
            gd_client.ClientLogin(
                username,
                password,
                "marmir-1.0")
        else:
            #TODO: use the token
            raise Exception("oauth not yet supported")

        ms = gdata.MediaSource(
            file_path=tmp_file_path,
            content_type='application/vnd.ms-excel')
        entry = gd_client.Upload(ms, name)  # NOQA

        #cleanup
        os.unlink(tmp_file_path)

        return gd_client.GetClientLoginToken()

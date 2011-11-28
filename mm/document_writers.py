from composer_xls import ComposerXLS

import os
import logging

log = logging.getLogger(__name__)

class DocumentWriter(object):
    "runs a composer"
   

    composer = None

    def writestr(self):
        if not self.composer:
            # default format is XLS
            self.composer = ComposerXLS(self.data_model, self.grid, self)
            log.info("Setting output format to XLS")
    

        return self.composer.run()


    def write(self, filename):
        ext = os.path.splitext(filename)[-1].lower()
        if ext == "xls":
            self.composer = ComposerXLS(self.data_model, self.grid, self)
            log.info("Setting output format to XLS, based on file extension")


        f = open(filename, "w")
        f.write(self.writestr())
        f.close()
        log.info("wrote file: %s" % filename)



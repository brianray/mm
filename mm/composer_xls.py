from composer_base import ComposerBase
import lib.xlwt_0_7_2 as xlwt
from lib.font_data.core import get_string_width
from lib.xldate.convert import to_excel_from_C_codes
import logging
import StringIO
import model_base
import style_base
import color_converter

log = logging.getLogger(__name__)


def get_string_width_from_style(char_string, style):
    point_size = style.font.height / 0x14  # convert back to points
    font_name = style.font.name
    if not font_name:
        font_name = 'Arial'
    return int(get_string_width(font_name, point_size, char_string) * 50)


class styleXLS(style_base.StyleBase):

    font_points = 12

    def get_pattern(self):
        pattern = xlwt.Pattern()
        pattern.pattern = 1
        if self.background_color:
            color = color_converter.get_closest_rgb_match(self.background_color)
        else:
            color = 1

        pattern.pattern_fore_colour = color
        return pattern

    def get_font_color(self):
        color = 0
        if self.color:
            color = color_converter.get_closest_rgb_match(self.color)
        return color

    def get_border(self):
        border = xlwt.Borders()
        if False:  # TODO borders
            border.left = border.right = border.top = border.bottom = 3000
            if self.border_color:
                color = color_converter.get_closest_rgb_match(self.border_color)
                border.top_color = color
                border.bottom_color = color
                border.left_color = color
                border.right_color = color
        return border

    def is_bold(self):
        if self.font_style == 'bold':
            return True
        return False

    def get_font_points(self):
        if self.font_size:
            return self.font_size
        return 12  # TODO: default from config?

    def get_font_name(self):
        if not self.font_family:
            return 'Arial'
        return self.font_family

    def get_text_align(self):
        text_align = xlwt.Alignment()
        # HORZ - (0-General, 1-Left, 2-Center, 3-Right, 4-Filled, 5-Justified, 6-CenterAcrossSel, 7-Distributed)
        horz = 0
        if self.text_align == 'center':
            horz = 2
        elif self.text_align == 'right':
            horz = 3
        elif self.text_align == 'left':
            horz = 1  # left
        else:
            log.warn("Unknown text_align %s" % self.text_align)

        text_align.horz = horz
        return text_align


class ComposerXLS(ComposerBase):

    def convert_style(self, stylestr):
        in_style = styleXLS()
        in_style.style_from_string(stylestr)

        style = xlwt.XFStyle()
        fnt1 = xlwt.Font()
        fnt1.name = in_style.get_font_name()
        fnt1.bold = in_style.is_bold()
        fnt1.height = in_style.get_font_points() * 0x14
        fnt1.colour_index = in_style.get_font_color()
        style.font = fnt1
        style.alignment = in_style.get_text_align()
        style.pattern = in_style.get_pattern()
        style.borders = in_style.get_border()

        return style

    def cell_to_value(self, cell, row_id):

        if self.document.config.headers and row_id == 0:
            css_like_style = self.document.config.header_style
        elif len(self.document.config.row_styles) == 0:
            css_like_style = ''
        else:
            style_index = row_id % len(self.document.config.row_styles)
            css_like_style = self.document.config.row_styles[style_index]

        style = self.convert_style(css_like_style)

        if type(cell) == model_base.HeaderFieldType:
            style = self.convert_style(self.document.config.header_style)
            return cell.data, style

        elif type(cell) in (model_base.IntFieldType, model_base.StringFieldType):
            return cell.data, style

        elif type(cell) == model_base.DateTimeFieldType:
            style.num_format_str = self.document.config.get('datetime_format', 'M/D/YY h:mm')
            return cell.data, style
        elif type(cell) == model_base.DateFieldType:
            num_string_format = self.document.config.get('date_format', 'M/D/YY')
            if cell.format:
                num_string_format = to_excel_from_C_codes(cell.format, self.document.config)
            style.num_format_str = num_string_format
            return cell.data, style

        else:
            return cell.data, style

    def start_new_row(self, id):
        pass

    def end_row(self, id):
        pass

    def write_cell(self, row_id, col_id, cell):

        value, style = self.cell_to_value(cell, row_id)
        if type(cell) == model_base.ImageFieldType:
            if cell.width:
                self.sheet.col(col_id).width = cell.width * 256
            if cell.height:
                self.sheet.col(col_id).height = cell.height * 256
            self.sheet.insert_bitmap(value, row_id, col_id)

        elif type(cell) == model_base.URLFieldType:
            self.sheet.write(
                row_id,
                col_id,
                xlwt.Formula('HYPERLINK("%s";"%s")' % (value, cell.displayname)),
                style
            )

        else:
            # most cases
            self.sheet.write(row_id, col_id, value, style)
        self.done_write_cell(row_id, col_id, cell, value, style)

    def done_write_cell(self, row_id, col_id, cell, value, style):

        if self.document.config.get('adjust_all_col_width', False):

            current_width = self.sheet.col_width(col_id) + 0x0d00
            log.info("current width is %s" % current_width)
            new_width = None

            if type(cell) == model_base.StringFieldType:
                new_width = get_string_width_from_style(value, style)

            elif type(cell) == model_base.DateTimeFieldType:
                new_width = 6550  # todo: different date formats

            elif type(cell) == model_base.URLFieldType:
                new_width = get_string_width_from_style(cell.displayname, style)

            if new_width and new_width > current_width:
                log.info("setting col #%s form width %s to %s" % (col_id, current_width, new_width))
                col = self.sheet.col(col_id)
                if new_width > 65535:  # USHRT_MAX
                    new_width = 65534
                    current_width = new_width
                col.width = new_width

    def set_option(self, key):

        val = getattr(self.document.config, key)
        if key == 'freeze_col' and val and val > 0:
            self.sheet.panes_frozen = True
            self.sheet.vert_split_pos = val

        elif key == 'freeze_row' and val and val > 0:
            self.sheet.panes_frozen = True
            self.sheet.horz_split_pos = val

        else:

            log.info("Nothing to be done for %s" % key)

            return
        log.info("Set option %s" % key)

    def run(self):

        self.w = xlwt.Workbook(style_compression=2)
        self.sheet = self.w.add_sheet('Sheet 1')
        if self.document.config.headers:
            self.write_header()
        self.iterate_grid()
        self.finish()

        # write the file to string
        output = StringIO.StringIO()
        self.w.save(output)
        contents = output.getvalue()
        output.close()

        return contents

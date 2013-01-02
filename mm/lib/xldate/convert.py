import re


class UnsupportedFormatCodeException(Exception):
    pass

def to_excel_from_C_codes(cdate_str, config):
    """
    ref http://office.microsoft.com/en-us/excel-help/create-a-custom-number-format-HP010342372.aspx
    and http://docs.python.org/2/library/datetime.html

    """
    pairs = (

    ('%a', None, "abbreviated weekday names require special function in excel"), # not supported
	('%A', None, "weeday naes require a special funtion in excel"), # "
	('%b', 'mmm'), # month as an abbreviation (Jan to Dec).
	('%B', 'mmmm'), # month as a full name (January to December)
	('%c', config.get('datetime_format', 'M/D/YY h:mm:ss') ), # date and time representation.
	('%d', 'dd'),
	('%f', '[ss].00'), #  Microsecond as a decimal number [0,999999], zero-padded on the left || Elapsed time (seconds and hundredths)  3735.80 [ss].00
	('%H', 'hh'), # Hours   00-23   hh
	('%I', None, "AM or PM required for 12 hour clock"), # AM or PM required
	('%j', None, "Day of year not supported in Excel"),
	('%m', 'mm'),
	('%M', 'mm'),
	('%p', 'AM/PM'), # 
	('%S', 'ss'),
	('%U', None, "Excel has no support for week number"),
	('%w', None, "Excel has no support for week day"),
	('%W', None, "Excel has no support for Week Number of year"),
	('%x', config.get('datetime_format', 'M/D/YY') ), # date 
	('%X', config.get('time_format', 'h:mm:ss') ), # time
	('%y', 'yy'), #  year as a two-digit number.
	('%Y', 'yyyy'), #  year as a four-digit number.
	('%z', None, "Excel has no time zone support"),
	('%Z', None, "Excel has no time zone support"),
	('%%', r'\%'),
)

    original_str = cdate_str
    for t in pairs:    
        if not t[1] and cdate_str.find(t[0]) > -1:
            reason = "Excel does not support"
            if len(t) > 2:
                reason = t[2]
            raise UnsupportedFormatCodeException("Could not replace %s (%s) found in %s" % (t[0], 
                                                                      reason, 
                                                               original_str))
        elif not t[1]:
            continue

        cdate_str = re.sub(t[0], t[1], cdate_str)

    return cdate_str







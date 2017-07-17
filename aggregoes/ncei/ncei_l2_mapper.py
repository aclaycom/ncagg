import os
import glob
from datetime import datetime
import json
import pkg_resources

"""
Implements get_files_for, get_runtime_config, and get_output_filename for l2 products at NCEI using
our specified structure and flow inside /nfs/goesr_private/.
"""

# in_base is expected to point to a directory containing directories named equivalently to the keys in mapping
in_base = os.environ.get("l2_aggregation_in_base", "/nfs/goesr_private/internal/aggregation/workspace/l2/data/")
# out_base is expected to point to a directory where directories and sat/product/year/month/ directories will
# be created below it as necessary
out_base = os.environ.get("l2_aggregation_out_base", "/nfs/goesr_private/l2/data/")


mapping = {
    ## MAG
    "magn-l2-hires": {
        "time": {
            "index_by": "time",
            "expected_cadence": {"time": 10},
        }
    },
    "magn-l2-avg1m": {
        "time": {
            "index_by": "time",
            "expected_cadence": {"time": 1.0/60.},
        }
    },
    "magn-l2-quiet": {
        "time": {
            "index_by": "time",
            "expected_cadence": {"time": 10},
        }
    },

    ## EXIS
    "xrsf-l2-flx1s": {
        "time": {
            "index_by": "time",
            "expected_cadence": {"time": 1},
        }
    },
    "xrsf-l2-avg1m": {
        "time": {
            "index_by": "time",
            "expected_cadence": {"time": 1.0/60.},
        }
    },

    ## SEIS
    "mpsh-l2-avg5m": {
        "record_number": {
            "index_by": "L2_SciData_TimeStamp",
            "expected_cadence": {"record_number": 1.0 / (60.0 * 5.0)}
        }
    },
    "sgps-l2-avg5m": {
        "record_number": {
            "index_by": "L2_SciData_TimeStamp",
            "expected_cadence": {"record_number": 1.0 / (60.0 * 5.0)}
        }
    }
}


def get_files_for(sat, product, dt, env="dr"):
    """
    
    :param sat: which goes sat, eg goes16
    :param product: L1b product type
    :type dt: datetime
    :param dt: datetime specification of day to get files for
    :param env: env to look for products in, defualt OR for L1b
    :return: list of files matching query
    """
    # check inputs
    check_product(product)
    check_sat(sat)
    case_insensitive_product = "".join(['[%s%s]' % (c.lower(), c.upper()) if c.isalpha() else c for c in product])
    path = os.path.join(in_base, sat, product, dt.strftime("%Y/%m/%d"), "%s_%s_*.nc" % (env, case_insensitive_product))
    return sorted(glob.glob(path))


def get_runtime_config(product):
    # check inputs
    check_product(product)
    return mapping[product]


def get_product_config(product):
    check_product(product)
    config = pkg_resources.resource_filename("aggregoes", "ncei/config/%s.json" % product)
    with open(config) as config_file:
        return json.load(config_file)


def get_output_filename(sat, product, datestr, env="xx", path=None):
    # check inputs
    assert int(datestr), "datestr should be numerical %Y, %Y%m, or %Y%m%d"
    check_product(product)
    check_sat(sat)
    if len(datestr) == 4:  # is a year file
        agg_length_prefix = "y"
        # put all year files in the product directory
        path_from_base = os.path.join(sat, product)
    elif len(datestr) == 6:  # is a month file
        agg_length_prefix = "m"
        # put all month files in the year directory
        path_from_base = os.path.join(sat, product, datestr[:4])
    elif len(datestr) == 8:  # is a day file
        agg_length_prefix = "d"
        # put all date files in a month directory
        path_from_base = os.path.join(sat, product, datestr[:4], datestr[4:6])
    else:
        raise ValueError("Unknown datestr: %s, expected %Y, %Y%m, or %Y%m%d")
    # create base of path if it doesn't exist already
    path = os.path.join(out_base, path_from_base) if path is None else path
    if not os.path.exists(path):
        os.makedirs(path)
    filename_sat = "g%s" % int(sat[-2:])
    filename = "%s_%s_%s_%s%s.nc" % (env, product, filename_sat, agg_length_prefix, datestr)
    return os.path.join(path, filename)


def check_sat(sat):
    """
    Validate sat string.
    
    :type sat: str
    :param sat: a satellite
    :return: None
    """
    assert sat.startswith("goes"), "Unknown satellite: %s" % sat


def check_product(product):
    """
    Validate product string.
    :param product: 
    :return: 
    """
    assert product in mapping.keys(), "Unknown L1b product: %s" % product


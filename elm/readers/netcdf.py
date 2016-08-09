from __future__ import print_function

import netCDF4 as nc
from affine import Affine

from elm.readers.util import (geotransform_to_bounds)


def _nc_str_to_dict(nc_str):
    '''helper func for splitting nc strings
    '''
    str_list = [g.split('=') for g in nc_str.split(';\n')]
    return dict([g for g in str_list if len(g) == 2])


def _assert_nc_attr(nc_dataset, attr_name):
    assert attr_name in nc_dataset.ncattrs(), 'NetCDF Header {} not found'.format(attr_name)


def _get_grid_headers(nc_dataset):
    _assert_nc_attr(nc_dataset, 'Grid.GridHeader')
    return _nc_str_to_dict(nc_dataset.getncattr('Grid.GridHeader'))


def _get_nc_attrs(nc_dataset):
    '''
    what metadata does the hdf4 test return

    '''
    _assert_nc_attr(nc_dataset, 'Grid.GridHeader')
    _assert_nc_attr(nc_dataset, 'HDF5_GLOBAL.FileHeader')
    _assert_nc_attr(nc_dataset, 'HDF5_GLOBAL.FileInfo')

    grid_header = _nc_str_to_dict(nc_dataset.getncattr('Grid.GridHeader'))
    file_header = _nc_str_to_dict(nc_dataset.getncattr('HDF5_GLOBAL.FileHeader'))
    file_info = _nc_str_to_dict(nc_dataset.getncattr('HDF5_GLOBAL.FileInfo'))

    return {**grid_header, **file_header, **file_info}  # PY3 specific - should this change?


def _get_bandmeta(nc_dataset):
    _assert_nc_attr(nc_dataset, 'Grid.GridHeader')
    return _nc_str_to_dict(nc_dataset.getncattr('Grid.GridHeader'))


def _get_geotransform(nc_info):

    # rotation not taken into account
    x_range = (float(nc_info['WestBoundingCoordinate']), float(nc_info['EastBoundingCoordinate']))
    y_range = (float(nc_info['SouthBoundingCoordinate']), float(nc_info['NorthBoundingCoordinate']))

    aform = Affine(float(nc_info['LongitudeResolution']), 0.0, x_range[0],
                   0.0, -float(nc_info['LongitudeResolution']), y_range[1])

    return aform.to_gdal()


def _get_subdatasets(nc_dataset):
    sds = []
    for k in nc_dataset.variables.keys():
        var_obj = nc_dataset.variables[k]
        obj = {d: var_obj.getncattr(d) for d in var_obj.ncattrs()}
        sds.append(obj)
    return sds


def load_netcdf_meta(datafile):
    '''
    loads metadata for NetCDF

    Parameters
    -------
    datafile - str: Path on disk to NetCDF file

    Returns
    -------
    Dictionary of metadata
    '''
    ras = nc.Dataset(datafile)
    attrs = _get_nc_attrs(ras)
    geotrans = _get_geotransform(attrs)
    x_size = ras.dimensions['lon'].size  # TODO: remove hardcoded lon variable name
    y_size = ras.dimensions['lat'].size  # TODO: remove hardcoded lat variable name

    meta = {'MetaData': attrs,
            'BandMetaData': _get_bandmeta(ras),
            'GeoTransform': geotrans,
            'SubDatasets': _get_subdatasets(ras),
            'Bounds': geotransform_to_bounds(x_size, y_size, geotrans),
            'Height': y_size,
            'Width': x_size,
            'Name': datafile,
            }
    return meta

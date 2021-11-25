from typing import _TypingEmpty, _tp_cache, Generic, get_type_hints
from pyspark.sql import DataFrame
import inspect

def _get_columns_dtypes(p):
    columns = set()
    dtypes = {}

    if isinstance(p, str):
        columns.add(p)
    elif isinstance(p, slice):
        columns.add(p.start)
        if not inspect.isclass(p.stop):
            raise TypeError("Column type hints must be classes, error with %s" % repr(p.stop))
        dtypes[p.start] = p.stop
    elif isinstance(p, (list, set)):
        for el in p:
            subcolumns, subdtypes = _get_columns_dtypes(el)
            columns |= subcolumns
            dtypes.update(subdtypes)
    elif isinstance(p, DatasetMeta):
        columns |= p.columns
        dtypes.update(p.dtypes)
    else:
        raise TypeError("Dataset[col1, col2, ...]: each col must be a string, list or set.")

    return columns, dtypes

class DatasetMeta(type):
    def __new__(metacls, name, bases, namespace, **kargs):
        return super().__new__(metacls, name, bases, namespace)

    @_tp_cache
    def __getitem__(self, parameters):
        if hasattr(self, '__origin__') and (self.__origin__ is not None or self._gorg is not Dataset):
            return super().__getitem__(parameters)
        if parameters == ():
            return super().__getitem__((_TypingEmpty,))
        if not isinstance(parameters, tuple):
            parameters = (parameters,)
        parameters = list(parameters)

        only_specified = True
        if parameters[-1] is ...:
            only_specified = False
            parameters.pop()

        columns, dtypes = _get_columns_dtypes(parameters)

        meta = DatasetMeta(self.__name__, self.__bases__, {})
        meta.only_specified = only_specified
        meta.columns = columns
        meta.dtypes = dtypes

        return meta

class DataFrame(DataFrame, extra=Generic, metaclass=DatasetMeta):
    """Defines type Dataset to serve as column name & type enforcement for pandas DataFrames"""

    def __new__(cls, *args, **kwds):
        if not hasattr(cls, '_gorg') or cls._gorg is Dataset:
            raise TypeError("Type Dataset cannot be instantiated; "
                            "use pandas.DataFrame() instead")
        return _generic_new(pd.DataFrame, cls, *args, **kwds)
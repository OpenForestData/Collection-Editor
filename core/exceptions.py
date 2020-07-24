class WrongAction(Exception):
    """
    Exception returned when DatatableAction is of invalid type
    """
    pass


class WrongFileType(Exception):
    """
    Exception returned when uploaded file is of unsupported type
    """
    pass

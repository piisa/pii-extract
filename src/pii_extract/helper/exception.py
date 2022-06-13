class PiiFinderException(Exception):
    def __init__(self, msg, *args):
        super().__init__(msg.format(*args))

class InvArgException(PiiFinderException):
    pass


class PiiUnimplemented(PiiFinderException):
    pass


class CountryNotAvailable(PiiUnimplemented):
    pass


class LangNotAvailable(PiiUnimplemented):
    pass

# old name
PiiManagerException = PiiFinderException

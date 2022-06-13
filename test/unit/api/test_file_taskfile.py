import tempfile

import pytest

from pii_extract import PiiEnum
from pii_extract.api import process_file, PiiFinder
from pii_extract.api.file import read_taskfile, add_taskfile
from pii_extract.helper.exception import InvArgException


from auxmock import mock_timestamp, mock_uuid
from datafile import datafile, readfile


# ----------------------------------------------------------------------

def test10_taskfile():
    """
    Read a taskfile
    """
    taskfile = datafile("taskfile.json")
    tasklist = read_taskfile(taskfile)
    assert len(tasklist) == 3
    assert tasklist[0]["pii"] == PiiEnum.IP_ADDRESS
    assert tasklist[1]["pii"] == PiiEnum.BITCOIN_ADDRESS
    assert tasklist[2]["pii"] == PiiEnum.CREDIT_CARD


def test11_taskfile_error():
    """
    Read a taskfile with an error
    """
    taskfile = datafile("taskfile-error.json")
    with pytest.raises(InvArgException):
        read_taskfile(taskfile)


def test12_taskfile():
    """
    Read a taskfile
    """
    taskfile = datafile("taskfile.json")
    proc = PiiFinder("en")
    add_taskfile(taskfile, proc)
    got = proc.task_info()
    exp = {
        (PiiEnum.CREDIT_CARD, None): [("standard credit card", "credit card number detection")],
        (PiiEnum.BITCOIN_ADDRESS, None): [
            ("bitcoin address", "bitcoin address detection")
        ],
        (PiiEnum.IP_ADDRESS, None): [
            ("regex for ip_address", "ip address detection via regex")
        ],
    }
    print(exp, got, sep="\n")
    assert exp == got


def test13_taskfile_err():
    """
    Read a taskfile, try to add to an object with a language mismatch
    """
    taskfile = datafile("taskfile.json")
    proc = PiiFinder("fr")
    with pytest.raises(InvArgException):
        add_taskfile(taskfile, proc)


def test20_taskfile(mock_timestamp, mock_uuid):
    """
    Read a taskfile, process data
    """
    with tempfile.NamedTemporaryFile(suffix='.json') as f:
        stats = process_file(
            datafile("minidoc-example.yaml"), f.name,
            "en", taskfile=datafile("taskfile.json")
        )
        exp = {"calls": 1, "CREDIT_CARD": 1, "BITCOIN_ADDRESS": 1}
        assert stats == exp

        exp = readfile(datafile("minidoc-pii-1.json"))
        got = readfile(f.name)
        # print(got)
        assert got == exp

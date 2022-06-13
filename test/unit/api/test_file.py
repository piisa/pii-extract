from pathlib import Path
import tempfile
import datetime

from unittest.mock import Mock
import pytest

from pii_data.types import PiiEnum
from pii_data.types import piicollection
from pii_extract.api import process_file

from auxmock import mock_timestamp, mock_uuid
from datafile import datafile, readfile



# -------------------------------------------------------------------------

def test10_process(mock_timestamp, mock_uuid):
    """
    Test processing a document
    """
    with tempfile.NamedTemporaryFile(suffix='.json', delete=True) as f:
        tasks = [PiiEnum.CREDIT_CARD, PiiEnum.BITCOIN_ADDRESS]
        stats = process_file(datafile("minidoc-example.yaml"), f.name,
                             "en", tasks=tasks)
        exp = {"calls": 1, "CREDIT_CARD": 1, "BITCOIN_ADDRESS": 1}
        assert stats == exp

        exp = readfile(datafile("minidoc-pii-1.json"))
        got = readfile(f.name)
        # print(got)
        assert got == exp


def test20_process(mock_timestamp, mock_uuid):
    with tempfile.NamedTemporaryFile(suffix='.json', delete=True) as f:
        tasks = [PiiEnum.CREDIT_CARD, PiiEnum.BITCOIN_ADDRESS,
                 PiiEnum.PHONE_NUMBER]
        stats = process_file(datafile("minidoc-example.yaml"), f.name,
                             "en", tasks=tasks)
        exp = {"calls": 1, "CREDIT_CARD": 1, "BITCOIN_ADDRESS": 1,
               "PHONE_NUMBER": 1}
        assert stats == exp

        exp = readfile(datafile("minidoc-pii-2.json"))
        got = readfile(f.name)
        # print(got)
        assert got == exp


"""
File-based API
"""

import sys
import json
from pathlib import Path

from typing import Dict, List, TextIO, Iterable, Optional, Union

from pii_data.types import PiiEnum, PiiEntity, SourceDocument

from pii_data.helper.io import openfile

from ..helper.exception import PiiFinderException, InvArgException
from ..helper.types import TYPE_STR_LIST
from . import PiiFinder

TYPE_RESULT = Union[str, Iterable[PiiEntity]]


def print_tasks(proc: PiiFinder, out: TextIO):
    print("\n. Installed tasks:", file=out)
    for (pii, country), doc in proc.task_info().items():
        print(f" {pii.name}  [country={country}]\n   ", doc, file=out)


def read_taskfile(filename: str) -> List[Dict]:
    """
    Read a list of task descriptors from a JSON file
    """
    with open(filename, encoding="utf-8") as f:
        try:
            tasklist = json.load(f)
            for td in tasklist:
                td["pii"] = PiiEnum[td["pii"]]
            return tasklist
        except json.JSONDecodeError as e:
            raise InvArgException("invalid task spec file {}: {}", filename, e)
        except KeyError as e:
            if str(e) == "pii":
                raise InvArgException(
                    "missing 'pii' field in task descriptor in {}", filename
                )
            else:
                raise InvArgException(
                    "cannot find PiiEnum element '{}' for task descriptor in {}",
                    e,
                    filename,
                )
        except Exception as e:
            raise InvArgException("cannot read taskfile '{}': {}", filename, e)


def add_taskfile(filename: TYPE_STR_LIST, proc: PiiFinder):
    """
    Add all tasks defined in a JSON file (or several) to a processing object
    """
    if isinstance(filename, (str, Path)):
        filename = [filename]
    for name in filename:
        tasklist = read_taskfile(name)
        proc.add_tasks(tasklist)


# ----------------------------------------------------------------------


def process_file(
    infile: str,
    outfile: str,
    lang: str,
    country: List[str] = None,
    tasks: List[str] = None,
    all_tasks: bool = False,
    taskfile: TYPE_STR_LIST = None,
    outfmt: str = None,
    debug: bool = False,
    show_tasks: bool = False,
    show_stats: bool = False,
) -> Dict:
    """
    Process a number of PII tasks on a source file
    """
    # Create the object
    proc = PiiFinder(
        lang,
        country,
        tasks,
        all_tasks=all_tasks,
        debug=debug
    )
    if taskfile:
        add_taskfile(taskfile, proc)
    if show_tasks:
        print_tasks(proc, sys.stderr)

    if outfmt is None:
        if outfile.endswith('.json'):
            outfmt = 'json'
        elif outfile.endswith('.ndjson'):
            outfmt = 'ndjson'

    # Process the file
    print(". Reading from:", infile, file=sys.stderr)
    print(". Writing to:", outfile, file=sys.stderr)

    doc = SourceDocument()
    doc.load(infile)

    piic = proc(doc)
    with openfile(outfile, "wt") as fout:
        piic.dump(fout, format=outfmt)

    if show_stats:
        print("\n. Statistics:", file=sys.stderr)
        for k, v in proc.stats.items():
            print(f"  {k:20} :  {v:5}", file=sys.stderr)

    return proc.stats

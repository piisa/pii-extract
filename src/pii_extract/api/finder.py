"""
Definition of the main PiiManager object
"""

from collections import defaultdict
from itertools import chain

from typing import Iterable, Tuple, List, Callable, Union, Dict, Type

from pii_data.types import SourceDocument, PiiEnum, PiiCollection

from ..helper import get_taskdict, country_list
from ..helper.taskdict import task_check
from ..helper.base import BasePiiTask, CallablePiiTask, RegexPiiTask
from ..helper.exception import InvArgException
from ..lang import LANG_ANY, COUNTRY_ANY


DEFAULT_TEMPLATES = {"replace": "<{name}>", "tag": "<{name}:{value}>"}


# --------------------------------------------------------------------------


def fetch_all_tasks(
    lang: str, country: Iterable[str] = None, debug: bool = False
) -> Iterable[List[Dict]]:
    """
    Return all processing tasks available for a given language & (optionally)
    country
    """
    taskdict = get_taskdict(debug=debug)
    # Language-independent
    for task in taskdict[LANG_ANY].values():
        yield task

    langdict = taskdict.get(lang, {})
    # Country-independent
    for task in langdict.get(COUNTRY_ANY, {}).values():
        yield task
    # Country-specific
    if country:
        if country[0] in (COUNTRY_ANY, "all"):
            country = country_list(lang)
        for c in country:
            if c == COUNTRY_ANY:  # already included above
                continue
            for task in langdict.get(c, {}).values():
                yield task


def fetch_task(
    taskname: str, lang: str, country: Iterable[str] = None, debug: bool = False
) -> Iterable[List[Dict]]:
    """
    Return a specific task for a given language & country
    (try to find the most specific task available)
    """
    found = 0
    taskdict = get_taskdict(debug=debug)
    if isinstance(taskname, PiiEnum):
        taskname = taskname.name

    langdict = taskdict.get(lang, {})
    if langdict:
        # First try: language & country
        if country:
            if country[0] in (COUNTRY_ANY, "all"):
                country = country_list(lang)
            for c in country:
                task = langdict.get(c, {}).get(taskname)
                if task:
                    found += 1
                    yield task
        # Second try: only language
        task = langdict.get(COUNTRY_ANY, {}).get(taskname)
        if task:
            found += 1
            yield task
    # Third try: generic task
    task = taskdict[LANG_ANY].get(taskname)
    if task:
        found += 1
        yield task

    # We didn't find anything
    if not found:
        print(f"Warning: cannot find any pii task for {taskname}, {lang}, {country}")


# --------------------------------------------------------------------------


def build_task(task: Dict) -> BasePiiTask:
    """
    Build a task object from its task descriptor
    """
    # Prepare arguments
    try:
        ttype, tobj = task["type"], task["task"]
        args = {k: task[k] for k in ("pii", "lang", "country", "name", "doc")}
        args["context"] = task.get("context")
        kwargs = task.get("kwargs", {})
    except KeyError as e:
        raise InvArgException("invalid pii task object: missing field {}", e)

    # Instantiate
    if ttype == "PiiTask":
        proc = tobj(**args)
    elif ttype == "callable":
        proc = CallablePiiTask(tobj, extra_kwargs=kwargs, **args)
    elif ttype in ("re", "regex"):
        proc = RegexPiiTask(tobj, **args, **kwargs)
    else:
        raise InvArgException(
            "invalid pii task type for {}: {}", task["pii"].name, ttype
        )
    return proc


# --------------------------------------------------------------------------


class PiiFinder:
    def __init__(
        self,
        lang: str,
        country: List[str] = None,
        tasks: Iterable[PiiEnum] = None,
        all_tasks: bool = False,
        debug: bool = False,
    ):
        """
        Initalize a processor object, loading & initializing all specified
        processing tasks
        """
        # Sanitize input
        self.lang = lang.lower()
        if isinstance(country, str):
            country = [country]
        self.country = [c.lower() for c in country] if country else None

        # Get the list of tasks we will use
        if all_tasks:
            tasklist = fetch_all_tasks(self.lang, self.country, debug=debug)
        elif tasks:
            if isinstance(tasks, PiiEnum):
                tasks = [tasks]
            tl = (fetch_task(name, self.lang, self.country) for name in tasks)
            tasklist = chain.from_iterable(tl)
        else:
            tasklist = []

        # Build an ordered array of task processors
        taskproc = (build_task(t) for t in chain.from_iterable(tasklist))
        self.tasks = sorted(taskproc, key=lambda e: e.pii.value)
        self.stats = defaultdict(int)


    def __repr__(self) -> str:
        return f"<PiiManager (tasks: {len(self.tasks)})>"


    def add_tasks(self, tasklist: Iterable[Dict]):
        """
        Add a list of processing tasks to the object
        """
        for task_spec in tasklist:
            task_check(task_spec, self.lang, self.country)
            self.tasks.append(build_task(task_spec))
        self.tasks = sorted(self.tasks, key=lambda e: e.pii.value)

    def get_plugins():
        """
        Get the list of all installed Pii plugins
        """
        pass

    def task_info(self) -> Dict[Tuple, Tuple]:
        """
        Return a dictionary with all defined tasks:
          - keys are tuples (task id, country)
          - values are tuples (name, doc)
        """
        info = defaultdict(list)
        for task in self.tasks:
            info[(task.pii, task.country)].append((task.name, task.doc))
        return info


    def __call__(self, doc: SourceDocument) -> PiiCollection:
        """
        Process a document, calling all defined anonymizers
        """
        return self.process_extract(doc)


    def process_extract(self, doc: SourceDocument) -> PiiCollection:
        """
        Process a document, calling all defined processors and performing
        PII extraction
        """
        self.stats["calls"] += 1

        piic = PiiCollection(lang=self.lang, docid=doc.id)
        for chunk in doc:
            for task_proc in self.tasks:
                elem_list = task_proc(chunk.text, chunk.id)
                for pii in elem_list:
                    piic.add(pii)
                    self.stats[pii.type.name] += 1
        return piic

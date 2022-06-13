import logging
import sys
import pkg_resources


from typing import List, Dict

PLUGIN_ID = 'pii_extract.plugin'


LOGGER = logging.getLogger(__name__)


def list_plugins(lang: str) -> List[Dict]:
    print(sys.path)
    plugins = []
    full_env = pkg_resources.Environment()
    distlist, errors = pkg_resources.working_set.find_plugins(full_env)
    for dist in distlist:
        entry_points = dist.get_entry_map().get(PLUGIN_ID, [])
        #print(dist, dist.project_name, dist.version, entry_points)
        for entry_point in entry_points:
            LoaderClass = dist.load_entry_point(PLUGIN_ID, entry_point)
            plugin = LoaderClass(lang)
            plugins.append({'name': dist.project_name,
                            'version': dist.version,
                            'description': plugin.description(),
                            'loader': plugin})
    return plugins



def load_plugins(self, lang: str, country: List[str] = None):
    '''
    Check available plugins and create an instance
    '''
    for plugin in list_plugins(lang):
        pass

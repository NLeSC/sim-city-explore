# SIM-CITY explore
#
# Copyright 2015 Joris Borgdorff <j.borgdorff@esciencecenter.nl>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import picas


class Ensemble(picas.Document):

    def __init__(self, name, parameter_specs):
        self.name = name
        self.specs = parameter_specs


def ensemble_view(task_db, name, version, url, ensemble = None):
    if ensemble is None:
        design_doc = '{0}_{1}'.format(name, version)
        ensemble_condition = ''
    else:
        design_doc = '{0}_{1}_{2}'.format(name, version, ensemble)
        ensemble_condition = ' && doc.ensemble === "{0}"'.format(ensemble)

    doc_id = '_design/{0}'.format(design_doc)
    try:
        task_db.get(doc_id)
    except:
        if not url.endswith('/'):
            url = url + '/'

        map_fun = '''
    function(doc) {{
      if (doc.type === "task" && doc.name === "{name}" &&
          doc.version === "{version}"{ensemble_condition}) {{
        emit(doc._id, {{
          id: doc._id,
          rev: doc._rev,
          url: "{url}/" + doc._id,
          error: doc.error,
          lock: doc.lock,
          done: doc.done,
          input: doc.input
        }});
      }}
    }}'''.format(name=name, version=version,
                 ensemble_condition=ensemble_condition, url=url)

        task_db.add_view('all_docs', map_fun, design_doc=design_doc)

    return design_doc

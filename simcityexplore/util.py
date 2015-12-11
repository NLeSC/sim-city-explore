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

import progressbar


class ProgressBar(progressbar.ProgressBar):
    ''' ProgressBar with increment and ETA. '''
    def __init__(self, size=None, **kwargs):
        ''' Size is total size of progressbar, other args are passed on. '''
        super(ProgressBar, self).__init__(
            maxval=size,
            widgets=[progressbar.Percentage(), ' ', progressbar.Bar('=', '[', ']'),
                     ' ', progressbar.widgets.ETA()],
            **kwargs)

    def increment(self):
        self.update(self.curval + 1)

    @classmethod
    def iterate(cls, iterator, size=None, **kwargs):
        if size is None:
            size = len(iterator)
        return cls(size=size, **kwargs)(iterator)

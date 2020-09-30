# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Alexander Jung <alexander.jung@neclab.eu>
#
# Copyright (c) 2020, NEC Europe Laboratories GmbH., NEC Corporation.
#                     All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
from __future__ import absolute_import
from __future__ import unicode_literals

from git import GitCommandError
from git import Repo as GitRepo
from git.cmd import Git as GitCmd

from .provider import LibraryProvider
from kraft.const import GIT_BRANCH_PATTERN
from kraft.const import GIT_TAG_PATTERN
from kraft.const import GIT_UNIKRAFT_TAG_PATTERN
from kraft.const import UNIKRAFT_ORIGIN
from kraft.const import VSEMVER_PATTERN
from kraft.logger import logger


def git_probe_remote_versions(source=None):  # noqa: C901
    """
    List references in a remote repository.

    Args:
        source:  The remote repository to probe.

    Returns:
        Dictionary of versions and their git shas.
    """

    versions = {}

    if source is None:
        return versions

    if source.startswith("file://"):
        source = source[7:]

    g = GitCmd()

    logger.debug("Probing remote git repository: %s..." % source)

    try:
        g.ls_remote(source)

    except GitCommandError as e:
        logger.fatal("Could not connect to repository: %s" % str(e))
        return versions

    for refs in g.ls_remote(source).split('\n'):
        hash_ref_list = refs.split('\t')

        # Empty repository
        if len(hash_ref_list) == 0 or hash_ref_list[0] == '':
            continue

        # Check if branch
        ref = GIT_BRANCH_PATTERN.search(hash_ref_list[1])

        if ref:
            ver = ref.group(1)
            if VSEMVER_PATTERN.search(ver):
                ver = ver[1:]

            versions[ver] = hash_ref_list[0]
            continue

        # Check if version tag
        if source.startswith(UNIKRAFT_ORIGIN):
            ref = GIT_UNIKRAFT_TAG_PATTERN.search(hash_ref_list[1])

        else:
            ref = GIT_TAG_PATTERN.search(hash_ref_list[1])

        if ref:
            ver = ref.group(1)
            if VSEMVER_PATTERN.search(ver):
                ver = ver[1:]

            versions[ver] = hash_ref_list[0]

    return versions


class GitLibraryProvider(LibraryProvider):

    @classmethod
    def is_type(cls, source=None):
        if source is None:
            return False

        try:
            if source.startswith("file://"):
                source = source[7:]

            GitRepo(source, search_parent_directories=True)
            return True

        except Exception:
            pass

        try:
            GitCmd().ls_remote(source)
            return True

        except Exception:
            pass

        return False

    def probe_remote_versions(self, source=None):
        if source is None:
            source = self.source

        return git_probe_remote_versions(source)

    def version_source_url(self, varname=None):
        return self.source

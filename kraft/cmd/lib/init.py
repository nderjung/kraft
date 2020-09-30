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

import os
import sys
import click

from pathlib import Path
from git import GitConfigParser
from configparser import NoOptionError
from configparser import NoSectionError

import kraft.util as util

from kraft.lib import Library
from kraft.error import KraftError
from kraft.error import CannotConnectURLError
from kraft.error import UnknownLibraryProvider
from kraft.logger import logger

from kraft.manifest import Manifest

from kraft.const import GITCONFIG_GLOBAL
from kraft.const import GITCONFIG_LOCAL
from kraft.const import URL_VERSION


@click.pass_context
def kraft_lib_init(ctx, libdir=None, name=None, author_name=None,
        author_email=None, origin_url=None, origin_version=None,
        provide_main=False, dependencies=list(), force_create=False,
        no_input=False, soft_pack=False):
    """
    """

    if libdir is None:
        raise ValueError("Cannot initialize library at unset directory")
    if origin_url is None:
        raise ValueError("expected origin url")


    lib = Library(
        name=name,
        localdir=libdir,
        origin_url=origin_url,
        origin_version=origin_version
    )

    lib.set_template_value('author_name', author_name)
    lib.set_template_value('author_email', author_email)
    lib.set_template_value('provide_main', provide_main)

    # if dependencies is not None:
    #     library.set_template_value('kconfig_dependencies', dependencies)

    lib.init(
        no_input=no_input,
        force_create=force_create
    )

    if soft_pack:
        manifest = Manifest(
            origin = "file://%s" % lib.localdir
        )

        print(lib.description)

        # item = ManifestItem(
        #     provider=ListProviderType.GITHUB, 
        #     name=name,
        #     description=lib.description,
        #     type=,
        #     dist=UNIKRAFT_RELEASE_STAGING,
        # )

        # manifest.add_item(item)


@click.command('init', short_help='Initialize a new Unikraft library.')  # noqa: C901
@click.option(
    '--author-name', '-a', 'author_name',
    help='The author\'s name for library.',
    metavar="NAME"
)
@click.option(
    '--author-email', '-e', 'author_email',
    help='The author\'s email for library.',
    metavar="EMAIL"
)
@click.option(
    '--version', '-v', 'origin_version',
    help='Set the known version of the library.',
    metavar="VERSION"
)
@click.option(
    '--origin', '-s', 'origin_url',
    help='Source code origin URL.  Use %s in the URL for automatic versioning.' % URL_VERSION
)
@click.option(
    '--with-main', '-m', 'provide_main',
    help='Provide a main function override.',
    is_flag=True
)
# @click.option(
#     '--with-dependencies', '-d', 'dependencies',
#     help='Select known library dependencies.',
#     multiple=True
# )
@click.option(
    '--workdir', '-w', 'workdir',
    help='Specify an alternative directory for the library (default is cwd).',metavar="PATH"
)
@click.option(
    '--force', '-F', 'force_create',
    help='Overwrite any existing files.',
    is_flag=True
)
@click.option(
    '--no-prompt', '-q', 'no_input',
    help='Do not prompt for additional data.',
    is_flag=True
)
@click.option(
    '--soft-pack', '-S', 'soft_pack',
    help="Softly pack the component so that it is available via kraft.",
    is_flag=True
)
@click.argument('name', required=False)
@click.pass_context
def cmd_lib_init(ctx, name=None, author_name=None, author_email=None,
        origin_version=None, origin_url=None, provide_main=False,
        workdir=None, force_create=False, no_input=False,
        soft_pack=False):
    """
    Initialize a new Unikraft library.
    """
    dependencies=list() # TODO
    
    if workdir is None and name is None:
        libdir = os.getcwd()
        name = os.path.basename(libdir)
        
    elif workdir is None:
        libdir = os.path.join(os.getcwd(), name)

    elif name is None:
        libdir = workdir
        name = os.path.basename(libdir)

    # Check if the directory is non-empty and prompt for validation
    if util.is_dir_empty(libdir) is False and ctx.obj.assume_yes is False:
        if click.confirm('%s is a non-empty directory, would you like to continue?' % libdir):  # noqa: E501
            force_create = True
        else:
            logger.critical("Cannot create directory: %s" % libdir)
            sys.exit(1)

    gitconfig = None

    try:
        if author_name is None or author_email is None:
            # Attempt reading author and email from .git/config
            if os.path.exists(os.path.join(libdir, '.git')):
                gitconfig = GitConfigParser(
                    [os.path.normpath(os.path.join(libdir, GITCONFIG_LOCAL))],
                    read_only=True
                )

            # Attempt reading default author and email from ~/.gitconfig
            else:
                gitconfig = GitConfigParser(
                    [os.path.normpath(os.path.expanduser(GITCONFIG_GLOBAL))],
                    read_only=True
                )

        if author_name is None:
            author_name = gitconfig.get("user", "name")

        if author_email is None:
            author_email = gitconfig.get("user", "email")
            
    except (NoSectionError, NoOptionError):
        pass
    
    if no_input is False:
        if origin_url is None:
            origin_url = click.prompt("source (Use %s for automatic versioning)" % URL_VERSION)

    try:
        kraft_lib_init(
            name=name,
            libdir=libdir,
            author_name=author_name,
            author_email=author_email,
            origin_url=origin_url,
            origin_version=origin_version,
            dependencies=dependencies,
            provide_main=provide_main,
            force_create=force_create,
            no_input=no_input,
            soft_pack=soft_pack
        )
    except Exception as e:
        logger.critical(str(e))

        if ctx.obj.verbose:
            import traceback
            logger.critical(traceback.format_exc())

        sys.exit(1)

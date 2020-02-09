# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Alexander Jung <alexander.jung@neclab.eu>
#
# Copyright (c) 2020, NEC Europe Ltd., NEC Corporation. All rights reserved.
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

import subprocess

from kraft.logger import logger

QEMU_GUEST='qemu-guest'
XEN_GUEST='xen-guest'

class Executor(object):
    _base_cmd = ''
    _cmd = []

    def __init__(self, kernel=None, architecture=None, platform=None):
        self._cmd = ['-k', kernel]
        self._kernel = kernel
        self._architecture = architecture
        self._platform = platform
    
    def add_initrd(self, initrd=None):
        if initrd:
            self._cmd.extend(('-i', initrd))

    def add_virtio_nic(self, virtio_nic=None):
        if virtio_nic:
            self._cmd.extend(('-n', virtio_nic))

    def add_bridge(self, bridge=None):
        if bridge:
            self._cmd.extend(('-b', bridge))

    def add_interface(self, interface=None):
        if interface:
            self._cmd.extend(('-V', interface))

    def add_block_storage(self, block_storage=None):
        if block_storage:
            self._cmd.extend(('-d', block_storage))

    def open_gdb(self, port=None):
        if port and isinstance(port, int):
            self._cmd.extend(('-g', port))

    def execute(self, extra_args=None, background=False, paused=False, dry_run=False):
        if background:
            self._cmd.append('-X')
        if paused:
            self._cmd.append('-P')
        if dry_run:
            self._cmd.append('-D')
        if extra_args:
            self._cmd.extend(('-a', extra_args))
        
        # TODO: This sequence needs to be better throughout as a result of the 
        # provisioning of `plat-` repositories will have their own runtime
        # mechanics.  For now this is "hard-coded":
        if self._platform == 'xen':
            cmd = [XEN_GUEST]
            cmd.extend(self._cmd)
        elif self._platform == 'linuxu':
            cmd = [
                self._kernel
            ]
            cmd.extend(extra_args)
        else:
            cmd = [QEMU_GUEST]
            cmd.extend(self._cmd)

        logger.debug('Running: %s' % ' '.join(cmd))
        subprocess.run(cmd)
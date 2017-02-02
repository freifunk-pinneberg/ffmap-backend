import subprocess
import json
import os


class Alfred(object):
    """
    Bindings for the alfred-json utility
    """
    def __init__(self, unix_sockpath=None):
        self.unix_sock = unix_sockpath
        if unix_sockpath is not None and not os.path.exists(unix_sockpath):
            raise RuntimeError('alfred: invalid unix socket path given')

    def _fetch(self, data_type):
        cmd = ['alfred-json',
               '-z',
               '-f', 'json',
               '-r', str(data_type)]
        if self.unix_sock:
            cmd.extend(['-s', self.unix_sock])

        # There should not be any warnings which would be sent by cron
        # every minute. Therefore suppress error output of called program
        FNULL = open(os.devnull, 'w')
        output = subprocess.check_output(cmd, stderr=FNULL)
        close(FNULL)
        return json.loads(output.decode("utf-8")).values()

    def nodeinfo(self):
        return self._fetch(158)

    def statistics(self):
        return self._fetch(159)

    def vis(self):
        return self._fetch(160)

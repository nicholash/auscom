
import re
import sys

class Namcouple:
    """
    Class to represent an OASIS namcouple file. 

    Allows fields to be modified.

    Presently only supports $RUNTIME
    """

    def __init__(self, filename):
        self.filename = filename
        with open(filename, 'r') as f:
            self.str = f.read()

    def set_runtime(self, runtime):

        m = re.search(r"^[ \t]*\$RUNTIME.*?^[ \t]*(\d+)", self.str, re.MULTILINE | re.DOTALL)
        assert(m is not None)
        self.str = self.str[:m.start(1)] + str(runtime) + self.str[m.end(1):]

    def set_ocean_timestep(self, timestep):

        def substitute_timestep(regex):
            """
            Make one change at a time, each change affects subsequent matches.
            """
            timestep_changed = False
            while True:
                matches = re.finditer(regex, self.str, re.MULTILINE | re.DOTALL)
                none_updated = True
                for m in matches:
                    if m.group(1) == timestep:
                        continue
                    else:
                        self.str = self.str[:m.start(1)] + timestep + self.str[m.end(1):]
                        none_updated = False
                        timestep_changed = True
                        break

                if none_updated:
                    break

            sys.stderr.write('WARNING: no timstep values were updated.\n')

        substitute_timestep(r"nt62 cice LAG=\+(\d+) ")
        substitute_timestep(r"cice nt62 LAG=\+(\d+) ")
        substitute_timestep(r"\d+ (\d+) \d+ INPUT/i2o.nc EXPORTED")
        substitute_timestep(r"\d+ (\d+) \d+ INPUT/o2i.nc EXPORTED")

    def write(self):
        with open(self.filename, 'w') as f:
            f.write(self.str)


class FortranNamelist:
    """
    Class to represent a Fortran namelist file.

    Can be used to modify fields.
    """

    def __init__(self, filename):
        self.filename = filename
        with open(filename, 'r') as f:
            self.str = f.read()

    def get_value(self, record, variable):
        """
        Return the value, start index and end index.
        """
        regex = r"%s[ \t]*=[ \t]*(\S*),?[ \t]*$"
        m = re.search((r"&%s.*?" + regex) % (record, variable), self.str, re.MULTILINE | re.DOTALL)
        assert(m is not None)

        return (m.group(1), m.start(1), m.end(1))

    def set_value(self, record, variable, value):

        (_, start, end) = self.get_value(record, variable)

        self.str = self.str[:start] + str(value) + self.str[end:]

    def write(self):
        with open(self.filename, 'w') as f:
            f.write(self.str)


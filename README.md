flockwave-mavlink
=================

This package adds MAVLink protocol support for Skybrush-related projects.
Right now it is essentially a re-packaging of the Python MAVLink classes
and functions generated by `pymavlink` because `pymavlink` is a mixture
of code generators, generated Python classes and several related utility
functions and scripts that we do not want to use, and it has several
dependencies like `future` and `lxml` that we do not want to include in a
distribution. This package provides the generated Python classes only in
a convenient Python wheel.

Future versions may add additional functions for parsing and sending MAVLink
messages; the development is currently driven by the needs of other Skybrush
projects, primarily Skybrush Server.

Usage
-----

The repository does _not_ include the code generated by `pymavlink` so a raw
checkout of the repository is not usable immediately. You need to run a script
to add the generated code:

```sh
$ python tools/generate-from-pymavlink.py
```

This will create a temporary directory and a virtualenv in it, install
`pymavlink` in the virtualenv, run the code generators, and then extract the
generated Python files into `src/flockwave/protocols/mavlink/dialects`.

If you use Poetry to manage a Python virtualenv corresponding to this project
(which you should), you can run ``./bootstrap.sh`` from the repo root to
update the generated files from the most recent `pymavlink` version
automatically.

License
-------

The _generated_ code in `src/flockwave/protocols/mavlink/dialects` is
licensed under the same conditions as the code generated by `pymavlink`
as it is essentially an almost verbatim copy with `black` formatting applied
on top of it.

Any additional code found in the package is licensed under the GNU General
Public License, version 3 or later. See `LICENSE.txt` for more details.


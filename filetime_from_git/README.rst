Use Git commit to determine page date
======================================

If your blog content is versioned via Git, this plugin will set articles'
and pages' ``metadata['date']`` to correspond to that of the Git commit.
This plugin depends on the ``gitpython`` python package, which can be
installed via::

    pip install gitpython

The date is determined via the following logic:

* if a file is not tracked by Git, or a file is staged but never committed
    - metadata['date'] = filesystem time
    - metadata['updated'] = filesystem time
* if a file is tracked, but no changes in staging area or working directory
    - metadata['date'] = first commit time
    - metadata['updated'] = last commit time
* if a file is tracked, and has changes in stage area or working directory
    - metadata['date'] = first commit time
    - metadata['updated'] = filesystem time

When this module is enabled, ``date`` and ``updated`` will be determined
by Git status; no need to manually set in article/page metadata. And
operations like copy and move will not affect the generated results.

Settings
--------

If you don't want a given article or page to use the Git time, set the
metadata to ``gittime: off`` to disable it.

You can also set ``GIT_FILETIME_FOLLOW`` to ``True`` in your settings to
make the plugin follow file renames — i.e., ensure the creation date matches
the original file creation date, not the date it was renamed.

If you have some articles which already have ``date`` or ``modified`` fields and you
want to preserve them, then set ``GIT_FILETIME_ONLY_IF_MISSING`` to ``True`` in your
Pelican config. By default, dates are always overwritten with those from Git.

By default, the plugin ensures that articles which use "git time" always have a
"Modified" date set, even if this date matches the creation date. If you only want
to add a "Modified" date if it actually differs from the creation date, then set
``GIT_FILETIME_ALWAYS_ADD_MODIFIED`` to ``False`` in your Pelican config.

FAQ
---

### Q. I get a GitCommandError: 'git rev-list ...' when I run the plugin. Why?
Be sure to use the correct gitpython module for your distro's Git binary.
Using the ``GIT_FILETIME_FOLLOW`` option to ``True`` may also make your
problem go away, as that optino uses a different method to find commits.

Some notes on Git
~~~~~~~~~~~~~~~~~~

* How to check if a file is managed by Git?

.. code-block:: sh

   git ls-files $file --error-unmatch

* How to check if a file has changes?

.. code-block:: sh

   git diff $file            # compare staging area with working directory
   git diff --cached $file   # compare HEAD with staged area
   git diff HEAD $file       # compare HEAD with working directory

* How to get commits related to a file?

.. code-block:: sh

   git status $file

With ``gitpython`` package, it's easier to parse committed time:

.. code-block:: python

   repo = Git.repo('/path/to/repo')
   commits = repo.commits(path='path/to/file')
   commits[-1].committed_date    # oldest commit time
   commits[0].committed_date     # latest commit time

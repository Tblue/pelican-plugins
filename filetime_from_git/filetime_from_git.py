# -*- coding: utf-8 -*-

import logging
import os
from pelican import signals, contents
from pelican.utils import strftime, set_date_tzinfo
from datetime import datetime
from git_wrapper import git_wrapper


logger = logging.getLogger(__name__)


def datetime_from_timestamp(timestamp, content):
    """
    Helper function to add timezone information to datetime,
    so that datetime is comparable to other datetime objects in recent versions
    that now also have timezone information.
    """
    return set_date_tzinfo(
        datetime.fromtimestamp(timestamp),
        tz_name=content.settings.get('TIMEZONE', None))


def filetime_from_git(content):
    if isinstance(content, contents.Static):
        logger.debug("Ignoring static content `%s'", content.source_path)
        return

    git = git_wrapper('.')
    tz_name = content.settings.get('TIMEZONE', None)

    # Do we want to retrieve the filetimes from Git?
    #
    # 1. The plugin can be disabled for a single content piece: If the content has a metadata field
    #    named "gittime" and this field is set to "off", "no" or "false" (case-insensitive), then
    #    we are not touching anything.
    gittime = content.metadata.get('gittime', 'yes').lower()
    gittime = gittime.replace("false", "no").replace("off", "no")
    if gittime == "no":
        logger.debug("Plugin explicitly disabled for `%s'", content.source_path)
        return

    # 2. Optionally, we only update those date fields which are not yet present.
    #    In other words, preserve the `date' and `modified' fields if they exist and fill them in
    #    from Git if they don't.
    only_missing_fields = content.settings.get("GIT_FILETIME_ONLY_IF_MISSING", False)
    if only_missing_fields and hasattr(content, "date") and hasattr(content, "modified"):
        logger.debug("`date' and `modified' fields are set for `%s', nothing to do.". content.source_path)
        return

    date = None
    modified = None

    # 1. file is not managed by git
    #    date: fs time
    # 2. file is staged, but has no commits
    #    date: fs time
    # 3. file is managed, and clean
    #    date: first commit time, update: last commit time or None
    # 4. file is managed, but dirty
    #    date: first commit time, update: fs time
    path = content.source_path
    if git.is_file_managed_by_git(path):
        commits = git.get_commits(
            path, follow=content.settings.get('GIT_FILETIME_FOLLOW', False))

        if len(commits) == 0:
            # never commited, but staged
            date = datetime_from_timestamp(
                os.stat(path).st_ctime, content)
        else:
            # has commited
            date = git.get_commit_date(
                commits[-1], tz_name)

            if git.is_file_modified(path):
                # file has changed
                modified = datetime_from_timestamp(
                    os.stat(path).st_ctime, content)
            else:
                # file is not changed
                if len(commits) > 1:
                    modified = git.get_commit_date(
                        commits[0], tz_name)
    else:
        # file is not managed by git
        date = datetime_from_timestamp(os.stat(path).st_ctime, content)

    if date is not None and (not hasattr(content, "date") or not only_missing_fields):
        # We got a creation date and the content either has no creation date set yet or
        # we want to override it.
        logger.debug("Setting `date' field from Git for `%s'", content.source_path)
        content.date = date

    if modified is not None and (not hasattr(content, "modified") or not only_missing_fields):
        # We got a modification date and the content either has no modification date set yet or
        # we want to override it.
        logger.debug("Setting `modified' field from Git for `%s'", content.source_path)
        content.modified = modified

    if not hasattr(content, 'modified'):
        content.modified = content.date

    # Make sure the `locale_date' field matches the `date' field:
    if hasattr(content, 'date'):
        content.locale_date = strftime(content.date, content.date_format)

    # Make sure the `locale_modified' field matches the `modified' field:
    if hasattr(content, 'modified'):
        content.locale_modified = strftime(
            content.modified, content.date_format)


def register():
    signals.content_object_init.connect(filetime_from_git)

#!/usr/bin/env python

import argparse
import fnmatch
import json
import logging
import os
import re
import sys

import bioblend.galaxy as bg

DefaultGalaxyUrl = "http://127.0.0.1:8080"

LogFormat = '%(levelname)s\t[ %(name)s ]\t%(message)s'
Log = logging.getLogger('ConfigGalaxy')

# Steps
StepWf = 'wf'

def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Upload the workflows from a directory into the specified Galaxy server")

    parser.add_argument('api_key', help="Master API key for Galaxy")
    parser.add_argument('username', help="Username for admin user")
    parser.add_argument('user_email', help="E-mail for admin user")
    parser.add_argument('user_password', help="Password for admin user (at least 6 characters)")

    parser.add_argument('--skip-steps', choices=(StepWf,),
                        help="Configuration steps to skip", default=list())
    parser.add_argument('--galaxy-url',
                        help="Galaxy URL (default: {})".format(DefaultGalaxyUrl),
                        default=DefaultGalaxyUrl)

    parser.add_argument('--workflow-dir',
                        help="Directory containing workflow files to be uploaded (must have .ga extension; default: '.')")

    options = parser.parse_args(args)

    Log.debug("Galaxy config running from %s", os.path.abspath('.'))
    if len(options.user_password) < 6:
        parser.error("Password needs to be at least 6 characters long.  User not added!")
    if not re.match(r'[^@]+@[^@]+\.[^@]+', options.user_email):
        parser.error("Email address has an invalid syntax.  User not added!")

    if StepWf not in options.skip_steps:
        if not options.workflow_dir:
            parser.error("You must specificy a workflow directory (unless you skip the workflow configuration step)")

        if not os.path.isdir(options.workflow_dir) or \
           not os.access(options.workflow_dir, os.R_OK | os.X_OK):
            parser.error("Specified workflow directory ({}) is either inaccessible or not readable".
                         format(options.workflow_dir))

    # This prints a password. Keep disabled unless debugging -> Log.debug("Parsed command line options:  %s", options)
    return options

def get_wf_files(wf_dir):
    for root, _, files in os.walk(wf_dir, followlinks=True):
        for f in fnmatch.filter(files, '*.ga'):
            yield os.path.join(root, f)

def upload_workflows(galaxy, wf_files):
    # We need to avoid uploading workflows that are already installed.
    # To do this, we query galaxy for its list of installed workflows and then
    # use that to filter.
    #
    # Getting all workflows is potentially bad (there could be a lot), at least
    # through bioblend, there currently is no way to query for specific workflows.
    # Note that `show_workflows` offers to query by name and id, but its implementation
    # actually queries all workflows and then filters on the client side.

    existing_workflows_by_uuid = { w['latest_workflow_uuid']: w for w in galaxy.workflows.get_workflows() }

    some_errors = False
    count = 0
    for filename in wf_files:
        try:
            with open(filename) as f:
                local_wf = json.load(f)
            installed_wf = existing_workflows_by_uuid.get(local_wf['uuid'])
            if installed_wf:
                Log.info("Skipping workflow file %s", os.path.basename(filename))
                Log.info("Workflow called '%s' with same uuid (%s) already installed",
                        installed_wf['name'], installed_wf['latest_workflow_uuid'])
            else:
                result = galaxy.workflows.import_workflow_json(local_wf)
                Log.info("Imported workflow '%s' with uuid %s.", result['name'], local_wf['uuid'])
                existing_workflows_by_uuid[local_wf['uuid']] = { # add new wf to our local dict
                        u'name': local_wf['name'],
                        u'latest_workflow_uuid': local_wf['uuid']
                }
                count += 1
        except (RuntimeError, StandardError) as e:
            Log.error("Error importing workflow file %s", filename)
            Log.exception(e)
            some_errors = True
    Log.info("Imported %d workflows into the instance", count)
    if some_errors:
        Log.error("Some workflows weren't imported because of errors")


def configure_admin_user(options):
    """
    Configures or retrieves the admin user.  Then creates a new api key for the user.

    If a new user user is created, this function will use
    `options.username`, `options.user_email`, `options.user_password`.
    If a user with a matching email already exists, this function will ensure that the
    username also matches and that it refers to an account with admin priviledges.
    """
    gi = bg.GalaxyInstance(options.galaxy_url, options.api_key)

    # Check if user already exists.  The API unfortunately doesn't currently
    # have a way to query by e-mail or by username.
    # If we ever redeploy the galaxy instance with the same DB this is potentially
    # a scalability issue, as we could in theory have any number of users.
    admin_user = None
    users = gi.users.get_users()
    for user in users:
        if user['email'] == options.user_email:
            Log.debug("Found user with matching email %s", user['email'])
            if user['username'] != options.username:
                raise RuntimeError(
                    "Found user with provided email ({}) but username ({}) doesn't match the one provided ({})".
                    format(options.user_email, user['username'], options.username))
            # get_users() returns partial records.  We need to get the user details
            user = gi.users.show_user(user['id'])
            if not user['is_admin']:
                raise RuntimeError("Found user with provided email ({}) but it does not have admin priviledges".
                                   format(options.user_email))

            Log.info("Admin user found with id %s", user['id'])
            admin_user = user
            break

    if admin_user is None:
        # create the admin user
        admin_user = gi.users.create_local_user(options.username, options.user_email, options.user_password)
        Log.info("Galaxy user %s created!", admin_user['username'])

    admin_user['api_key'] = gi.users.create_user_apikey(admin_user['id'])
    Log.info("Created API key for admin user %s", admin_user['email'])
    return admin_user

def main(args):
    options = parse_args(args)

    Log.info("Configuring admin user")
    admin_user = configure_admin_user(options)

    if StepWf not in options.skip_steps:
        Log.info("Adding workflows")
        gi = bg.GalaxyInstance(options.galaxy_url, admin_user['api_key'])
        wf_files = get_wf_files(options.workflow_dir)
        upload_workflows(gi, wf_files)
    else:
        Log.info("Skipping workflow configuration step by user request")

    Log.info("Galaxy configuration completed")

if __name__ == '__main__':
    logging.basicConfig(format=LogFormat, level=logging.DEBUG)
    try:
        main(sys.argv[1:])
    except (RuntimeError, StandardError) as e:
        Log.fatal("Error configuring the Galaxy instance")
        Log.exception(e)
        sys.exit(e)
    sys.exit(0)

from get_general_settings import *

import os
import pygit2

current_working_directory = os.path.dirname(__file__)
repository_path = pygit2.discover_repository(current_working_directory)
local_repo = pygit2.Repository(repository_path)

def check_and_apply_update(repo=local_repo, remote_name='origin'):
    for remote in repo.remotes:
        if remote.name == remote_name:
            remote.fetch()
            remote_id = repo.lookup_reference('refs/remotes/origin/' + branch).target
            merge_result, _ = repo.merge_analysis(remote_id)
            # Up to date, do nothing
            if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
                print 'Up to date'
                return
            # We can just fastforward
            elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
                repo.checkout_tree(repo.get(remote_id))
                master_ref = repo.lookup_reference('refs/heads/master')
                master_ref.set_target(remote_id)
                repo.head.set_target(remote_id)
            else:
                raise AssertionError('Unknown merge analysis result')

from get_general_settings import *

import os
import pygit2
import logging

current_working_directory = os.path.dirname(__file__)
repository_path = pygit2.discover_repository(current_working_directory)
local_repo = pygit2.Repository(repository_path)

def check_and_apply_update(repo=local_repo, remote_name='origin'):
    repo.config['remote.origin.fetch'] = '+refs/heads/*:refs/remotes/origin/*'
    repo.remotes[remote_name].fetch()
    repo.config['user.name'] = 'Bazarr user'
    repo.config['user.email'] ='bazarr@fakeuser.com'

    for remote in repo.remotes:
        if remote.name == remote_name:
            remote.fetch()
            remote_id = repo.lookup_reference('refs/remotes/origin/' + str(branch)).target
            merge_result, _ = repo.merge_analysis(remote_id)
            # Up to date, do nothing
            if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
                logging.info('No new version of Bazarr available.')
                pass
            # We can just fastforward
            elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
                repo.checkout_tree(repo.get(remote_id))
                master_ref = repo.lookup_reference('refs/remotes/origin/' + str(branch))
                master_ref.set_target(remote_id)
                repo.head.set_target(remote_id)
                logging.info('Bazarr updated to latest version and need to be restarted.')
                #os.execlp('python', 'python', os.path.join(os.path.dirname(__file__), 'bazarr.py'))
            # We can just do it normally
            elif merge_result & pygit2.GIT_MERGE_ANALYSIS_NORMAL:
                repo.merge(remote_id)
                print repo.index.conflicts

                assert repo.index.conflicts is None, 'Conflicts, ahhhh!'
                user = repo.default_signature
                tree = repo.index.write_tree()
                commit = repo.create_commit('HEAD',
                                            user,
                                            user,
                                            'Merge!',
                                            tree,
                                            [repo.head.target, remote_id])
                repo.state_cleanup()
                logging.error('Conflict detected when trying to update.')
                #os.execlp('python', 'python', os.path.join(os.path.dirname(__file__), 'bazarr.py'))
            # We can't do it
            else:
                logging.error('Bazarr cannot be updated: Unknown merge analysis result')

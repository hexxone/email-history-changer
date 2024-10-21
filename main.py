import io
import os
import platform
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

# Build Tree
# (github user)
# -> followers
#   -> repos
#     -> contributors
# -> following
#     -> contributors
# -> repos
#   -> contributors

import requests

from config import settings

time.sleep(1)
print("Config loaded.")
print("GitHub User: " + settings.github.username)
print("Scrape User: " + settings.github.scrape_user)

headers = {
    'Authorization': f'Bearer {settings.github.api_token}',
    'Accept': 'application/vnd.github.v3+json'
}

def decode(bytestr):
  'Try to convert bytestr to utf-8 for outputting as an error message.'
  return bytestr.decode('utf-8', 'backslashreplace')

class SubprocessWrapper(object):
  @staticmethod
  def decodify(args):
    if type(args) == str:
      return args
    else:
      assert type(args) == list
      return [decode(x) if type(x)==bytes else x for x in args]

  @staticmethod
  def call(*args, **kwargs):
    if 'cwd' in kwargs:
      kwargs['cwd'] = decode(kwargs['cwd'])
    return subprocess.call(SubprocessWrapper.decodify(*args), **kwargs)

  @staticmethod
  def check_output(*args, **kwargs):
    if 'cwd' in kwargs:
      kwargs['cwd'] = decode(kwargs['cwd'])
    return subprocess.check_output(SubprocessWrapper.decodify(*args), **kwargs)

  @staticmethod
  def check_call(*args, **kwargs): # pragma: no cover  # used by filter-lamely
    if 'cwd' in kwargs:
      kwargs['cwd'] = decode(kwargs['cwd'])
    return subprocess.check_call(SubprocessWrapper.decodify(*args), **kwargs)

  @staticmethod
  def Popen(*args, **kwargs):
    if 'cwd' in kwargs:
      kwargs['cwd'] = decode(kwargs['cwd'])
    return subprocess.Popen(SubprocessWrapper.decodify(*args), **kwargs)

subproc = subprocess
if platform.system() == 'Windows' or 'PRETEND_UNICODE_ARGS' in os.environ:
  subproc = SubprocessWrapper

def get_repos(user):
    url = f'https://api.github.com/users/{user}/repos'
    headers = {'Authorization': f'token {settings.github.api_token}'}
    response = requests.get(url, headers=headers)
    if response.status_code < 200 or response.status_code > 299:
        print("GitHub sent bad status code; " + response.text)
        exit(-1)

    repos = response.json()
    repo_data = []
    for repo in repos:
        if repo['fork']:
            # Fetch additional details about the parent repo
            parent_details_url = f"https://api.github.com/repos/{repo['full_name']}/"
            parent_response = requests.get(parent_details_url, headers=headers)
            if parent_response.ok:
                parent_repo_info = parent_response.json()
                parent_clone_url = parent_repo_info['clone_url']
            else:
                parent_clone_url = None
        else:
            parent_clone_url = None

        repo_data.append({
            'clone_url': repo['clone_url'],
            'is_fork': repo['fork'],
            'parent_clone_url': parent_clone_url
        })
    return repo_data


def get_contributor_emails(clone_url):
    # Extract the username from the clone_url
    github_username = clone_url.split('/')[3]

    repo_name = clone_url.split('/')[-1].replace('.git', '')
    clone_url_with_token = clone_url.replace('https://',
                                             f'https://{settings.github.username}:{settings.github.api_token}@')

    # Use the extracted github_username instead of settings.github.scrape_user
    if not os.path.exists(github_username):
        os.mkdir(github_username)

    if not os.path.exists(f'{github_username}/{repo_name}.git'):
        subprocess.run(['git', 'clone', '--bare', clone_url_with_token, f'{github_username}/{repo_name}.git'])

    cmd = f'git -C {github_username}/{repo_name}.git shortlog -e -s -n HEAD'
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    emails = set()

    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        email = line.split('<')[-1].strip().strip('>')
        emails.add(email)

    return emails

def main():
    repos = get_repos(settings.github.scrape_user)
    print(f'Found {len(repos)} repos.')

    contributors = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for repo in repos:
            if "three" not in repo['clone_url'] and "worker-loader" not in repo['clone_url']:
                future = executor.submit(get_contributor_emails, repo['clone_url'])
                futures[future] = repo

        for future in futures:
            emails = future.result()
            repo = futures[future]
            if repo['is_fork'] and repo['parent_clone_url']:
                # Handle forked repository
                parent_emails = get_contributor_emails(repo['parent_clone_url'])
                unique_emails = emails - parent_emails
            else:
                unique_emails = emails

            for email in unique_emails:
                if email not in contributors:
                    contributors[email] = set()
                contributors[email].add(repo['clone_url'])

    print("--- Unique Contributors (excluding parent repos) ---")
    for email, repos in contributors.items():
        print(f"{email}: contributed to {', '.join(repos)}")

if __name__ == '__main__':
    main()
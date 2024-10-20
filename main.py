import io
import os
import platform
import subprocess
import time

import requests

from config import settings

time.sleep(1)
print("Config loaded.")
print("GitHub User: " + settings.github.username)

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


def get_repos():
    url = f'https://api.github.com/users/{settings.github.username}/repos'
    response = requests.get(url, headers=headers)
    if response.status_code < 200 or response.status_code > 299:
        print("GitHub sent bad status code; " + response.text)
        exit(-1)

    repos = response.json()
    return [repo['clone_url'] for repo in repos if repo["fork"] is False]


def get_infos(contributors, clone_url):
    repo_name = clone_url.split('/')[-1].replace('.git', '')

    # E.g.: https://github.com/user/repo.git -> https://user:MYTOKEN@github.com/user/repo.git
    clone_url_with_token = clone_url.replace('https://', f'https://{settings.github.username}:{settings.github.api_token}@')

    print(f"$: git clone {clone_url}")
    cloned = subprocess.run(['git', 'clone', '--bare', clone_url_with_token, f'{repo_name}.git'])

    os.chdir(f'{repo_name}.git')

    print("$: git shortlog -e -s -n")
    cmd = ('git shortlog -e -s -n HEAD')
    proc = subproc.Popen(cmd, shell=True, bufsize=-1, stdout=subprocess.PIPE)

    # Process each line to extract the email and name
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        # Extract the email which is the last part inside <>
        email = line.split('<')[-1].strip('>').strip()
        # Extract the name which is between the commit count and the email
        name = " ".join(line.split()[1:-1])

        joined = name + " " + email

        # Add the tuple of name and email to the set
        contributors.add(joined)

    os.chdir('..')

    return contributors



def main():
    repos = get_repos()
    print(f'Found {str(len(repos))} repos.')
    contributors = set()
    for repo in repos:
        if "three" in repo:
            continue
        if "worker-loader" in repo:
            continue
        print(f'Getting infos from: {repo}')
        get_infos(contributors, repo)

    print("--- All Contributors ---")
    # Print all unique contributors
    for user in contributors:
        print(f"{user}")

if __name__ == '__main__':
    main()

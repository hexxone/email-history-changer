import io
import os
import platform
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

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
    return [repo['clone_url'] for repo in repos]


def get_infos(clone_url):
    repo_name = clone_url.split('/')[-1].replace('.git', '')
    clone_url_with_token = clone_url.replace('https://', f'https://{settings.github.username}:{settings.github.api_token}@')

    if not os.path.exists(f'{repo_name}.git'):
        print(f"$: git clone {clone_url}")
        subprocess.run(['git', 'clone', '--bare', clone_url_with_token, f'{repo_name}.git'])

    print("$: git shortlog -e -s -n")
    cmd = f'git -C {repo_name}.git shortlog -e -s -n HEAD'
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    contributors = {}

    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        email = line.split('<')[-1].strip().strip('>')
        name = " ".join(line.split()[1:-1])

        if email not in contributors:
            contributors[email] = set()

        contributors[email].add(name)

    # subprocess.run(['rm', '-rf', f'{repo_name}.git'])  # Clean up
    return contributors


def main():
    repos = get_repos()
    print(f'Found {len(repos)} repos.')

    # Filter out specific repos
    repos = [repo for repo in repos]

    contributors = {}
    counter = 0
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(get_infos, repo) for repo in repos]
        for future in futures:
            counter+=1
            repo_contributors = future.result()
            progress = "{:.9f}".format(100 / len(repos) * counter)
            print(f"--- Overall Progress: {progress} %")
            for email, names in repo_contributors.items():
                if email not in contributors:
                    contributors[email] = set()
                contributors[email].update(names)

    print("--- All Contributors ---")
    for email, names in contributors.items():
        print(f"{email}: {', '.join(names)}")

if __name__ == '__main__':
    main()
import io
import os
import platform
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pyvis.network import Network

os.environ["PATH"] += os.pathsep + 'D:/Projekte/Coding/python/email-history-changer/Graphviz-12.1.2-win64/bin'

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
print("Scrape Users: " + str(len(settings.github.scrape_users)))

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
    repos = []
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"GitHub sent bad status code; {response.text}")
            break
        batch = response.json()
        for repo in batch:
            print("Processing: " + repo['full_name'])
            repo_data = {
                'name': f"{user}/{repo['name']}",
                'clone_url': repo['clone_url'],
                'is_fork': repo['fork']
            }
            if repo['fork']:
                # Fetch additional details about the parent repo
                parent_details_url = f"https://api.github.com/repos/{repo['full_name']}"
                parent_response = requests.get(parent_details_url, headers=headers)
                if parent_response.ok:
                    parent_repo_info = parent_response.json()
                    repo_data['parent_clone_url'] = parent_repo_info['clone_url']
                else:
                    repo_data['parent_clone_url'] = None
            else:
                repo_data['parent_clone_url'] = None
            repos.append(repo_data)
        url = response.links.get('next', {}).get('url', None)
    return repos

def get_contributor_emails(clone_url):
    print("Analyzing: " + clone_url)
    github_username = clone_url.split('/')[3]
    repo_name = clone_url.split('/')[-1].replace('.git', '')
    local_repo_path = f'{github_username}/{repo_name}.git'

    if not os.path.exists(github_username):
        os.makedirs(github_username, exist_ok=True)

    if not os.path.exists(local_repo_path):
        subprocess.run(['git', 'clone', '--bare', clone_url, local_repo_path])

    emails = set()
    try:
        cmd = f'git -C {local_repo_path} shortlog -se HEAD'
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=60)

        lines = output.decode('utf-8').split('\n')

        for line in lines:
            email = line.split('<')[-1].strip('>\n')
            emails.add(email)
    except subprocess.TimeoutExpired:
        print("Analyzing timeout.")

    return emails


def visualize_network(contributors):
    net = Network('90vh', '100%', bgcolor="#222222", font_color="white", filter_menu=True)
    net.barnes_hut()

    connections = {}  # This will store the count of edges per node
    for email, repos in contributors.items():
        for repo in repos:
            if email in connections:
                connections[email].add(repo)
            else:
                connections[email] = {repo}
            if repo in connections:
                connections[repo].add(email)
            else:
                connections[repo] = {email}

    # Add nodes and edges based on connection count
    for email, connected_nodes in connections.items():
        if len(connected_nodes) >= 2:
            net.add_node(email, label=email, title=email)
    for repo, connected_nodes in connections.items():
        net.add_node(repo, label=repo, title=repo, shape='box')
    for email, repos in contributors.items():
        for repo in repos:
            if email in connections and len(connections[email]) >= 1:
                net.add_edge(email, repo)

    net.toggle_physics(True)
    # net.show_buttons(filter_=['physics'])
    net.set_options("""
const options = {
  "nodes": {
    "borderWidth": null,
    "borderWidthSelected": null,
    "font": {
      "size": 40
    },
    "scaling": {
      "min": 38,
      "max": 80
    },
    "size": null
  },
  "edges": {
    "color": {
      "inherit": true
    },
    "font": {
      "size": 48
    },
    "selfReferenceSize": null,
    "selfReference": {
      "angle": 0.7853981633974483
    },
    "smooth": {
      "forceDirection": "none"
    }
  },
  "physics": {
    "barnesHut": {
      "theta": 0.4,
      "gravitationalConstant": -75000,
      "centralGravity": 4.5,
      "springLength": 250,
      "springConstant": 0.001
    },
    "minVelocity": 0.75
  }
}
""")
    net.show("github_network.html", notebook=False)

def main():
    users = settings.github.scrape_users

    all_repos = sum([get_repos(u) for u in users], [])
    print(f"Found {len(all_repos)} repos across all users.")

    contributors = {}
    for repo in all_repos:
        emails = get_contributor_emails(repo['clone_url'])
        repo_name = repo['name']
        for email in emails:
            if email not in contributors:
                contributors[email] = set()
            contributors[email].add(repo_name)

    print("Visualizing... please wait")
    visualize_network(contributors)

if __name__ == '__main__':
    main()
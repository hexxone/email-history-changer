import os
import subprocess
import time
import requests
from pyvis.network import Network
from config import settings

time.sleep(1)
print("Config loaded.")
print("GitHub User: " + settings.github.username)
print("Scrape Users: " + str(len(settings.github.scrape_users)))

headers = {
    'Authorization': f'Bearer {settings.github.api_token}',
    'Accept': 'application/vnd.github.v3+json'
}

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
            repos.append((user, repo['clone_url'], repo['name']))  # Include repo name for clearer identification
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
        logs_exist = subprocess.run(['git', 'log', '-1'], cwd=local_repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if logs_exist.returncode == 0:
            output = subprocess.check_output('git shortlog -se HEAD', cwd=local_repo_path, stderr=subprocess.STDOUT, timeout=60)
            lines = output.decode('utf-8').split('\n')
            for line in lines:
                email = line.split('<')[-1].strip('>\n')
                emails.add(email)
    except subprocess.CalledProcessError:
        return "No commits available in the repository."
    except subprocess.TimeoutExpired:
        print("Analyzing timeout.")

    return emails

def visualize_network(user_repo_map, repo_contributors):

    net = Network('90vh', '100%', filter_menu=True)
    net.barnes_hut()

    added_nodes = set()  # To track added nodes

    for user, repos in user_repo_map.items():
        user_node_id = f"user_{user}"  # Unique node id for users
        if user_node_id not in added_nodes:
            net.add_node(user_node_id, label=user, title=user, shape="box", color="lightgreen")
            added_nodes.add(user_node_id)
        for repo in repos:
            repo_name = repo[2]  # Use the repository name for labeling
            repo_node_id = repo[1]  # Use the clone URL as unique ID
            if repo_node_id not in added_nodes:
                net.add_node(repo_node_id, label=repo_name, title=repo_name, shape="box", color="lightblue")
                added_nodes.add(repo_node_id)
            net.add_edge(user_node_id, repo_node_id)

            # Add contributors as edges to the repo
            if repo_node_id in repo_contributors:
                for email in repo_contributors[repo_node_id]:
                    if email not in added_nodes:
                        net.add_node(email, label=email, title=email)
                        added_nodes.add(email)
                    net.add_edge(email, repo_node_id)

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
      "size": 58
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
    net.show("github_network_test.html", notebook=False)

def main():
    users = settings.github.scrape_users
    print("Running....")

    user_repo_map = {}
    repo_contributors = {}
    for user in users:
        user_repos = get_repos(user)
        if user not in user_repo_map:
            user_repo_map[user] = []
        for user, clone_url, repo_name in user_repos:
            user_repo_map[user].append((user, clone_url, repo_name))
            # Collect contributors for each repo
            contributors = get_contributor_emails(clone_url)
            if clone_url not in repo_contributors:
                repo_contributors[clone_url] = set()
            for email in contributors:
                repo_contributors[clone_url].add(email)

    print("Visualizing... please wait")
    visualize_network(user_repo_map, repo_contributors)

if __name__ == '__main__':
    main()
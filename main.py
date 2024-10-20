import os
import subprocess
import time

import requests

from config import settings

time.sleep(1)
print("Config loaded.")
print("GitHub User: " + settings.github.username)
print("GitHub Commit Author: " + settings.github.commit_author)
print("GitHub Commit Email: " + settings.github.commit_email)
print("GitHub Old Emails: " + str(len(settings.github.old_emails)))

headers = {
    'Authorization': f'Bearer {settings.github.api_token}',
    'Accept': 'application/vnd.github.v3+json'
}

def add_mailmap_txt():
    with open('mailmap.txt', 'w') as f:
        f.write(f'{settings.github.commit_author} <{settings.github.commit_email}>\n')
        for mail in settings.github.old_emails:
            f.write(f'{settings.github.commit_author} <{settings.github.commit_email}> <{mail}>\n')


def set_git_config():
    subprocess.run([
        'git', 'config', '--global', 'user.name', f'"{settings.github.commit_author}"'
    ])
    subprocess.run([
        'git', 'config', '--global', 'user.email', f'{settings.github.commit_email}'
    ])

def get_repos():
    url = f'https://api.github.com/users/{settings.github.username}/repos'
    response = requests.get(url, headers=headers)
    if response.status_code < 200 or response.status_code > 299:
        print("GitHub sent bad status code; " + response.text)
        exit(-1)

    repos = response.json()
    return [repo['clone_url'] for repo in repos if repo['archived'] is False]


def change_email(clone_url):
    repo_name = clone_url.split('/')[-1].replace('.git', '')

    # E.g.: https://github.com/user/repo.git -> https://user:MYTOKEN@github.com/user/repo.git
    clone_url_with_token = clone_url.replace('https://', f'https://{settings.github.username}:{settings.github.api_token}@')

    print(f"$: git clone {clone_url_with_token}")
    subprocess.run(['git', 'clone', '--bare', clone_url_with_token, f'{repo_name}.git'])
    os.chdir(f'{repo_name}.git')

    print("$: python git-filter-repo --mailmap")
    subprocess.run([
        'python', '../git-filter-repo',
        '--mailmap', '../mailmap.txt'
    ])

    print("$: git push origin --all --force")
    subprocess.run(['git', 'push', 'origin', '--all', '--force'])

    os.chdir('..')


def main():
    subprocess.run(['rm', '-rf', '*.git'])
    add_mailmap_txt()
    set_git_config()
    repos = get_repos()
    print(f'Found {str(len(repos))} non-archived repos.')
    for repo in repos:
        print(f'Changing email-history in: {repo}')
        change_email(repo)
        time.sleep(3)


if __name__ == '__main__':
    main()

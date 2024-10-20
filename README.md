# email-history-changer

This tool is designed to help you automatically remove or replace old email addresses from your entire commit history 
across multiple GitHub repositories.
It's built with privacy and ease of use in mind, enabling you to update commit metadata across all your projects efficiently.

## About

Not a lot of people consciously know this, but all of your commit emails and names are publicly visible and can get scraped.

You can open any commit, simply append `.patch` to the url and see the author name and email in clear.

E.g.: <https://github.com/hexxone/email-history-changer/commit/b43c8c728982d5cc52a15759fb3c42dea9920639.patch>

Contains:
```
From b43c8c728982d5cc52a15759fb3c42dea9920639 Mon Sep 17 00:00:00 2001
From: "hexx.one" <5312542+hexxone@users.noreply.github.com>
Date: Sun, 20 Oct 2024 01:18:11 +0200
Subject: [PATCH] Initial commit
...
```

Once it has been on the internet, you should generally assume that the information cannot be deleted.
It has probably already been duplicated by someone or something, somewhere.
Take for example: <https://web.archive.org/>

So this tool can be more used as a "cleanup" for old/unwanted names etc. in all of your repos.

## Many words of caution

This is a purely "source-available" project. I.e.: I will not accept PRs, feature requests or bug reports.

You are on your own.

1. I do not accept any responsibility for damages caused by this tool!
2. Timetravel has not been invented yet! Make backups of everything before starting!
3. The tool cannot modify "Archived" repositories. You have to un-archive them, modify them, and archive them again.
4. The tool cannot modify "force-push protected" branches. You have to temporarily disable the rule.
5. If you made a PR to some other repo with a wrong email - you are out of luck. The repo owner would have to merge you modified history.
6. ALL FORKED Repos will also get out of sync and cannot easily be merged.
7. If you work in a team, inform your collaborators about these changes, they will need to re-clone the repository after the modification.
8. make sure to globally set your correct git config email & username from now on.

## Prerequisites

- read all of the above
- know what you are doing
- Docker

## Usage

- create a [new api token](https://github.com/settings/tokens) with repository & user read access (only used for enumerating your public & private projects)
  - copy `example.secrets.yaml` to `.secrets.yaml` and add your new token
- modify `settings.yaml`
  - your dedicated github-no-reply email address can be found on your profile settings
- run it with `docker compose up -d`

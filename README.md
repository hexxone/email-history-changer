# email-history-changer (grab)

This branch contains a tool for visualizing GitHub users, 
their repositories and related commit-emails and on which projects they collaborated.

It can also be used to determine which emails have been (unwanted) exposed by a user, 
so that it can be fixed with the email-history-changer (main branch).

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

## Prerequisites

- Docker

## Usage

- create a [new GitHub api token](https://github.com/settings/tokens) with repository & user read access (used for enumerating and cloning your public & private projects)
  - copy `example.secrets.yaml` to `.secrets.yaml` and add your new token
- modify `settings.yaml`
  - add GitHub usernames to scrape
- run it with `docker compose up -d`

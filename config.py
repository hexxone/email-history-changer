
from dynaconf import Dynaconf, Validator

settings = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_files=['settings.yaml', '.secrets.yaml'],
    validators=[
        Validator("github.username", ne=None),
        Validator("github.api_token", ne=None),
        Validator("github.commit_author", ne=None),
        Validator("github.commit_email", ne=None)
    ]
)

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load these files in the order.

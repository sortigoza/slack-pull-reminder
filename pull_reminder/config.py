import os
import logging

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """generic error for the config class"""


class Config:
    def __init__(self):
        self._load_slack_configs()
        self._load_github_configs()
        self.LOGLEVEL = os.environ.get("LOGLEVEL", logging.INFO)
        logger.setLevel(self.LOGLEVEL)

        logger.debug(vars(self))

    def _load_slack_configs(self):
        self.SLACK_API_TOKEN = os.environ.get("SLACK_API_TOKEN", "")
        self.SLACK_POST_URL = "https://slack.com/api/chat.postMessage"
        self.SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "#general")
        self.SLACK_INITIAL_MESSAGE = """\
Hi! There's a few open pull requests you should take a
look at:

"""

    def _load_github_configs(self):
        # required fields
        try:
            self.GITHUB_API_TOKEN = os.environ["GITHUB_API_TOKEN"]
            self.GITHUB_ORGANIZATION = os.environ["GITHUB_ORGANIZATION"]
        except KeyError as error:
            raise ConfigError("please set the environment variable %s", str(error))

        ignore = os.environ.get("IGNORE_TITLE_WORDS", "")
        self.IGNORE_TITLE_WORDS = [i.lower().strip() for i in ignore.split(",") if i]

        include_labels = os.environ.get("INCLUDE_LABELS", "")
        self.INCLUDE_LABELS = [
            i.lower().strip() for i in include_labels.split(",") if i
        ]

        repositories = os.environ.get("REPOSITORIES")
        self.REPOSITORIES = (
            [r.lower().strip() for r in repositories.split(",")] if repositories else []
        )

        usernames = os.environ.get("USERNAMES")
        self.USERNAMES = (
            [u.lower().strip() for u in usernames.split(",")] if usernames else []
        )

    def is_slack_configured(self):
        return (
            self.SLACK_API_TOKEN != ""
            and self.SLACK_POST_URL != ""
            and self.SLACK_CHANNEL != ""
        )

    def is_slack_text_output_configured(self):
        return True

    def is_stdout_configured(self):
        return True

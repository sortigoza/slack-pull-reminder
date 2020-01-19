import logging
from pprint import pprint
import requests

from pull_reminder.config import Config, ConfigError
from pull_reminder.github_data_provider import GitHubDataProvider

logging.basicConfig()
logger = logging.getLogger(__name__)


class PRFilter:
    def __init__(self, config):
        self._config = config

    def filter(self, pull):
        return self.is_valid_title(pull) and self.is_valid_labels(pull)

    def is_valid_title(self, pull):
        if not self._config.IGNORE_TITLE_WORDS:
            return True

        lowercase_title = pull.title.lower()
        for ignored_word in self._config.IGNORE_TITLE_WORDS:
            if ignored_word in lowercase_title:
                return False

        return True

    def is_valid_labels(self, pull):
        if not self._config.INCLUDE_LABELS:
            return True

        for label in pull.labels:
            lowercase_label = label.lower()
            for filtered_label in self._config.INCLUDE_LABELS:
                if filtered_label in lowercase_label:
                    return True

        return False


class SlackError(Exception):
    """generic error for slack"""


class Slack:
    def __init__(self, config):
        self._config = config

    def get_message_text(self, pull_requests):
        lines = self.format_message_lines(pull_requests)
        return self._config.SLACK_INITIAL_MESSAGE + "\n".join(lines)

    def send(self, pull_requests):
        text = self.get_message_text(pull_requests)
        logger.info("slack message:\n%s", text)

        payload = {
            "token": self._config.SLACK_API_TOKEN,
            "channel": self._config.SLACK_CHANNEL,
            "username": "Pull Request Reminder",
            "icon_emoji": ":bell:",
            "text": text,
        }
        logger.debug("slack payload: %s", payload)
        logger.info("sending slack message")

        response = requests.post(self._config.SLACK_POST_URL, data=payload)
        answer = response.json()
        if not answer["ok"]:
            raise SlackError(answer["error"])

    def format_message_lines(self, open_prs):
        return [
            self._format_pull_request(pull, owner=self._config.GITHUB_ORGANIZATION)
            for pull in open_prs
        ]

    def _format_pull_request(self, pull, owner=""):
        return f"*[{owner}/{pull.repository_name}]* <{pull.url}|{pull.title} - by {pull.creator}>"


class StdoutPrint:
    def __init__(self, config):
        self._config = config

    def send(self, pull_requests):
        from pytablewriter import UnicodeTableWriter

        value_matrix_nested = self.format_pr_values(pull_requests)
        value_matrix = [line for lines in value_matrix_nested for line in lines]

        writer = UnicodeTableWriter()
        writer.table_name = "open pull request to review"
        writer.headers = ["repository_name", "[pull.creator] pull.title / pull.url"]
        writer.value_matrix = value_matrix
        writer.margin = 1

        writer.write_table()

    def format_pr_values(self, open_prs):
        return [
            self._format_pull_request(pull, owner=self._config.GITHUB_ORGANIZATION)
            for pull in open_prs
        ]

    def _format_pull_request(self, pull, owner=""):
        return [
            [f"{owner}/{pull.repository_name}", f"[{pull.creator}] {pull.title}"],
            ["", pull.url],
        ]


def main():
    config = Config()
    github = GitHubDataProvider(config)
    slack = Slack(config)
    stdout_print = StdoutPrint(config)
    pr_filter = PRFilter(config)

    pull_requests = github.fetch_organization_pulls()

    pull_requests_filtered = [pr for pr in pull_requests if pr_filter.filter(pr)]

    if not pull_requests_filtered:
        logger.warning("no pull requests to send")
        return

    pprint(pull_requests_filtered)

    if config.is_stdout_configured():
        stdout_print.send(pull_requests_filtered)

    if config.is_slack_text_output_configured():
        print(slack.get_message_text(pull_requests_filtered))

    if config.is_slack_configured():
        slack.send(pull_requests_filtered)
    else:
        logger.warning("slack is not configured, message not sent")


if __name__ == "__main__":
    try:
        main()
    except ConfigError as err:
        logger.error(err)
        exit(1)

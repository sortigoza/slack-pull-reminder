from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

from pydantic import BaseModel
from toolz import partial, pipe, concat
from github3 import login


class PullRequest(BaseModel):
    class Config:
        allow_mutation = False

    repository_name: str
    creator: str
    url: str
    title: str
    age_hrs: int
    labels: List[str]
    mergeable: bool
    review_status: Dict
    pull_requests: Optional[Any]


class GitHubDataProvider:
    def __init__(self, config):
        self._config = config

    def fetch_organization_pulls(self):
        client = login(token=self._config.GITHUB_API_TOKEN)
        organization = client.organization(self._config.GITHUB_ORGANIZATION)
        return self.build_prs_state(organization)

    def build_prs_state(self, organization):
        return pipe(
            organization,
            self.get_organization_repos,  # => List[repositories]
            partial(
                filter, partial(self.is_required_fetch, self._config.REPOSITORIES)
            ),  # => List[repositories]
            partial(map, self._expand_repository_pulls),  # => List[List[Pulls]]
            concat,  # => List[Pulls]
        )

    def _expand_repository_pulls(self, repository):
        return pipe(
            repository,
            self.get_repository_open_prs,
            partial(map, partial(self.build_pr_object, repository)),
        )

    @staticmethod
    def get_organization_repos(organization):
        return organization.repositories()

    @staticmethod
    def is_required_fetch(required_repos, repository):
        return repository.name.lower() in required_repos

    @staticmethod
    def build_pr_object(repository, pull):
        return PullRequest(
            repository_name=repository.name,
            creator=pull.user.login,
            url=pull.html_url,
            title=pull.title,
            labels=GitHubDataProvider._get_pr_labels(pull),
            age_hrs=GitHubDataProvider._get_pr_age(pull),
            mergeable=pull.mergeable,
            review_status=GitHubDataProvider._get_pr_review_statuses(pull),
            pull_requests=None,
        )

    @staticmethod
    def get_repository_open_prs(repository):
        return [
            repository.pull_request(pull.number)
            for pull in repository.pull_requests()
            if pull.state == "open"
        ]

    @staticmethod
    def _get_pr_labels(pull):
        return [x["name"] for x in pull.labels]

    @staticmethod
    def _get_pr_age(pull):
        td = datetime.now(timezone.utc) - pull.updated_at
        hours, _ = divmod(int(td.total_seconds()), 3600)
        return hours

    @staticmethod
    def _get_pr_review_statuses(pull):
        review_statuses = {}

        for review in pull.reviews():
            if review.state not in review_statuses:
                review_statuses[review.state] = []
            review_statuses[review.state].append(review.user.login)

        return review_statuses

    def _get_repo_names(self, repos):
        return [repo.name for repo in repos]

    def _get_prs_titles(self, pull_requests):
        return [pull.title for pull in pull_requests]

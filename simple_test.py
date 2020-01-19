import json
from pprint import pprint
from pull_reminder.config import Config
from pull_reminder.github_data_provider import GitHubDataProvider, PullRequest

config = Config()
data = GitHubDataProvider(config)

# org_pulls = [dict(x) for x in data.fetch_organization_pulls()]
# org_pulls_json = json.dumps(org_pulls, indent=2)
# with open("output.json", "w") as f:
#     f.write(org_pulls_json)
# print(org_pulls_json)

with open("output.json", "r") as f:
    raw_data = json.loads(f.read())

data = [PullRequest(**x) for x in raw_data]
# pprint(data)

my_prs = [x for x in data if x.creator == "sortigoza"]
print("my PRs:\n")
pprint(my_prs)
print()


def involved(pr):
    for k, v in pr.review_status.items():
        if "sortigoza" in v:
            return True


my_prs = [x for x in data if involved(x)]
print("involved PRs:\n")
pprint(my_prs)
print()

import json
from pull_reminder.config import Config
from pull_reminder.github_data_provider import GitHubDataProvider

config = Config()
data = GitHubDataProvider(config)

org_pulls = [dict(x) for x in data.fetch_organization_pulls()]
org_pulls_json = json.dumps(org_pulls, indent=2)
with open("output.json", "w") as f:
    f.write(org_pulls_json)
print(org_pulls_json)

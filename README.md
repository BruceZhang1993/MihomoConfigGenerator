## MihomoConfigGenerator

### Usage

1. Fork this repository
2. Create a token from https://github.com/settings/tokens .
3. In repository settings, Actions -> General -> Workflow permissions, check `Read and write permissions`.
4. In repository settings, Secrets and variables -> Actions -> Secrets -> New repository secret, create a secret named `MY_TOKEN` and paste the token.
5. In repository settings, Secrets and variables -> Actions -> Variables -> New repository variable, create a variable named `TEMPLATE` and paste your rules config file.
6. Create a variable named `SUBSCRIPTIONS` and paste your subscription urls in json format, eg `["url1","url2"]`.
7. (Optional) Create a variable named `FILE` and paste the file content of more proxies not from subscription.
8. Create a tag named `pre-release` on this repository, and GitHub Actions will automatically release the config file.
9. Download config file and enjoy!

#### How to update subscription and rebuild
```shell
# Using github-cli
gh variable set SUBSCRIPTIONS '["url1","url2"]'
gh workflow run release.yml --ref pre-release
```

#### How to test latency of subscription before adding to configuation
```shell
poetry run mihomo_speedtest [URL]
```

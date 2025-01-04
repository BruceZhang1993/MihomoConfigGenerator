## MihomoConfigGenerator

### Usage

1. Fork this repository and make it private.
2. Create a token from https://github.com/settings/tokens .
3. In repository settings, Actions -> General -> Workflow permissions, check `Read and write permissions`.
4. In repository settings, Secrets and variables -> Actions -> Secrets -> New repository secret, create a secret named `MY_TOKEN` and paste the token.
5. In repository settings, Secrets and variables -> Actions -> Variables -> New repository variable, create a variable named `TEMPLATE` and paste your rules config file.
6. create a variable named `SUBSCRIPTIONS` and paste your subscription urls in json format, eg `["url1","url2""]`.
7. Create a tag named `pre-release` on this repository, and GitHub Actions will automatically release the config file.
8. Download config file and enjoy!
9. (Optionally) Create a cloudflare worker to fetch this file by url.

Cloudflare worker example:
https://gist.github.com/BruceZhang1993/ce1e5409764bb1a0d3c51a699e6f719d

Replace your username and repository name in the source code.

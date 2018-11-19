# Auto archiver for getpocket.com

## Usage

### Get Pocket access token

Visit the `/get-access-token` page, do the OAuth2 authorization flow and set the received access token to the `POCKET_ACCESS_TOKEN` environment variable.

### Archive old articles

`POST` to the `/archive-old-articles` url. It will archive the articles which as been added earlier then one week.
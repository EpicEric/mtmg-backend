# mtmg-backend

A very simple backend for [epiceric/mtmg.com.br](https://github.com/epiceric/mtmg.com.br), deployed on Heroku.

## Adding enigma

Get credentials from Heroku, log into `psql`, and run:

```psql
INSERT INTO enigma (secret, target_url, webhook_url) VALUES ('teste_segredo', 'google.com', 'some-webhook-url.com/...');
```

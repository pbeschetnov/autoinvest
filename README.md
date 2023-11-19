# AutoInvest

It's a bot that helps you dollar cost average into your favorite stocks and
ETFs. By using [Trading 212](https://www.trading212.com/invite/16aT36LLY8) as
a trading platform it can execute BUY orders of assets in a specific
[pie](https://helpcentre.trading212.com/hc/en-us/articles/360009313957-Pies-AutoInvest-Introduction).

While the platform itself provides autoinvest functionality, it is limited by
investing each Month/Week/Day. Also, it executes orders just as the exchanges
open, which sometimes can lead to buying for higher prices.

So if you want to invest more frequently automation can help here :)

The bot buys stocks according to "what pie to autoinvest", "amount to invest
each week" and other parameters. You can manage your pie in the T212 app, the
bot will pick it up and adjust investing schedule.

_Example_: a pie is set to 50% `VUSA` (S&P 500), 25% `AAPL` and 25% `GOOG`
allocations. Target spending amount is set to 1000 EUR weekly. The AutoInvest
bot will then invest 500 EUR into `VUSA`, 250 EUR into `AAPL` and `GOOG` each,
evenly splitting the amounts into hourly orders. Though, it doesn't take into
account currently owned assets' percentages of the portfolio.

## Components

The AutoInvest bot consists of two components (services):
- Main module that runs in a loop, updates the pie composition, schedules and
  executes orders.
- Telegram bot that you can use to enable/disable autoinvest or check status.
  Also, it will notify you about unexpected runtime errors.

## Requirements

- Have an account with
  [Trading 212](https://www.trading212.com/invite/16aT36LLY8)
- Set up a Telegram bot through [t.me/BotFather](https://t.me/BotFather)

## Installation and deployment

All the scripts is valid for using on an Ubuntu machine.

1. Copy code to your server and change dir to `autoinvest`.
2. Setup secrets in `.secrets` folder:
   1. ```bash
      mkdir .secrets
      chmod 0700 .secrets
      ```
   2. In this folder create files with credentials called:
      - t212_email — your T212 login email
      - t212_password — and password
      - t212_token — T212 API token, you can get it in the app (you can use
        a DEMO token too, just don't forget to update `MODE` in `config.py`)
      - pg_password — put any password here
      - telegram_user — your telegram ID, you can message your telegram bot,
        so it could detect it
      - telegram_token — your configured telegram bot token
3. Run `./install_packages.sh` to install packages and setup DB.
4. Run `./setup_services.sh` to deploy AutoInvest and the Telegram bot. The
   services will automatically restart if failures occur or after reboot.

## How to use

1. Review all the settings in the `config.py` file.
2. Create a pie with the name as in `AUTOINVEST_PIE` and fill it with stocks.
3. Enable AutoInvest by sending `/enable` command to your Telegram bot.
4. Profit! AutoInvest is now running and buying stocks regularly.

## Local run

1. In `deploy` folder run `docker-compose up --build` to quickly deploy the
   Postgres DB with all tables created.
2. Just run `pyhton main.py` to start AutoInvest or `python telegram.py` to
   start the Telegram bot.

To recreate DB tables run:
```bash
docker-compose down --volumes && docker-compose up --build
```

To connect to the DB use: 
```bash
PGPASSWORD=$(cat .secrets/pg_password | xargs) psql -U autoinvest -p 5432 -h 127.0.0.1 -d autoinvest
```
# 1. What It Does

wallet tracker is a bot that tracks your spending across a time period through your spending logs. e.g. you can set the budget to $100 per week, then every time you spend money, you do /log spend to keep track of it. At the end of the period, wallet will give you a summary of your spending.

The bot is currently inactive for lack of server hosting fees. [See production screenshots here](https://postimg.cc/gallery/6pgmfcs).

# 2. How to use

## 2.1. Initialise

`/quicksetup start` : Set up your budget, summary channel, and timezone in one go

## 2.2. Log

`/log spend` : Log a new spending entry

`/log list` : View your 10 most recent entries with their IDs

`/log edit` : Edit an existing entry by ID

`/log delete` : Delete an entry by ID (with confirmation)

## 2.3. Customise

`/budget set` : Set/Update your budget amount and period

`/budget setchannel` : Set/Update the channel for automatic summaries

`/summary show` : View your spending summary for the current period

`/summary settimezone` : Set/Update your local time zone for scheduled summaries

`/summary optout` : Stop receiving automatic summaries

`/summary optin` : Resume receiving automatic summaries

## 2.4. Other

`/ping` : Check if bot is online

`/help show` : Get a list of available commands

# 3. Warning

*By running the following command, you can be overwriting pre-existing data. No prompt asking if you’re sure for now so do it at your own risk.*

`/quicksetup start` 

`/log edit`

`/log delete` 

`/budget set`

`/budget setchannel`

`/summary settimezone`

*If you’re familiar with bots that work when you run commands in the DM between you and the bot, **this bot is not the case** and works in a server only. This feature will be implemented in a future update.*

*I’m on the free version of Railway that doesn’t have persistent storage, which means **every time a new update is published, all previous data is lost**. If you are one of the 3 people who actually use this bot, I will tell you when I publish an update, which I will try not not do so frequently.*

*Love,*

*Nicey*
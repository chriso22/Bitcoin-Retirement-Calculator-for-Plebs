# Bitcoin Retirement Savings Calculator for Plebs

How much bitcoin do you need to retire on, and what can you withdraw each month? Enter the bitcoin you hold today, a monthly dollar amount you will buy until you retire, and how many years the money has to last. The calculator shows the monthly withdrawal that covers those years and whether any bitcoin is left over.

**Live:** add your GitHub Pages link here once it is published.

## Daily investment brief

Open [`brief.html`](brief.html) for a personal daily watchlist snapshot covering **Bitcoin**, **MSTR** (Strategy), **ASST** (Strive), **XXI** (Twenty One Capital), **MRLN** (Merlin), **ASAT** (if quoted), and **SpaceX** (**SPCX**). Each card shows price, day change, a short sparkline, 52-week range, and a few recent headlines.

Refresh the snapshot locally with:

```bash
python3 scripts/refresh-brief.py
```

That writes `brief-data.json`. A GitHub Action (`.github/workflows/daily-brief.yml`) can run the same script on weekdays and commit updates. On the brief page, **Refresh Bitcoin price** still fetches a live BTC/USD quote from Coinbase (CoinGecko fallback), matching the calculator.

## What it models

Everything runs in steps of your choosing: daily, weekly or monthly (monthly is the default).

1. **Building the stack.** Each step until retirement you buy bitcoin with your buy amount at that step's price, minus the trading fee. The price compounds by one step of your projected growth rate. You can raise the buys with inflation.
2. **Retirement.** Each step you sell enough bitcoin to cover that step's withdrawal. You enter the withdrawal in today's dollars. The calculator inflates it to the year you retire, uses that larger figure as your first withdrawal, and keeps raising it with inflation so it holds its purchasing power.
3. **Tax and fees.** Tax applies only to the gain above your average cost basis, not to the whole sale. The cost basis blends what you already hold with what you buy along the way. The trading fee applies to both buys and sells.

### Inputs

| Input                                       | Meaning                                                                                            |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Bitcoin held today                          | The stack you start with                                                                           |
| Price today                                 | Type it in by hand, or click **Use live price** to fetch the current price (see below)             |
| How often you buy and withdraw              | Daily, weekly or monthly. Changing it converts your buy and withdrawal amounts to the new schedule |
| Buy each day / week / month                 | Dollars spent on bitcoin each step until you retire                                                |
| Years of buying                             | How long until you retire                                                                          |
| Raise buys with inflation                   | Optional. Grows the buy amount by the inflation rate                                               |
| Years the money must last                   | Length of retirement                                                                               |
| Withdrawal to test (per day, week or month) | In today's dollars. Leave at 0 to test the maximum                                                 |
| Bitcoin growth per year                     | Projected annual growth. Negative values are allowed                                               |
| Inflation per year                          | Applied to withdrawals (and to buys, if the option is on)                                          |
| Cost basis of what you hold                 | Average price you paid for your existing bitcoin                                                   |
| Tax on gains                                | Applied to the gain above your cost basis                                                          |
| Trading fee                                 | Percentage of each buy and each sale                                                               |

### Live price

The **Use live price** button under the price field fetches the current BTC/USD price from Coinbase. If Coinbase fails, it falls back to CoinGecko. The results recalculate as soon as the price comes back. If both lookups fail, the page tells you and keeps the price you had, so you can always type one in by hand.

### Outputs

- The monthly withdrawal, in today's dollars, that uses the whole stack over your chosen years
- Bitcoin at retirement, and its value in future and today's dollars
- Total bought, and average cost basis at retirement
- The most you could withdraw per month forever, when that is possible
- For a withdrawal you choose: what it equals in retirement-year dollars, whether it lasts, and how much bitcoin is left or when it runs out
- A chart of your bitcoin over time

### The "forever" figure

Withdrawing forever only works if bitcoin's growth outpaces inflation by enough to cover tax and fees. When it does not, the page says so instead of showing a number. Setting a finite number of years always works.

## What it does not model

It assumes bitcoin grows at a constant rate. Real prices swing widely, so a projection can be right about the average and still wrong about the path. There is no volatility, no drawdown or sequence-of-returns risk, no tax-lot accounting, and no borrowing against the stack. Treat the results as scenarios, not forecasts. This is arithmetic, not financial advice.

## Run it locally

There is nothing to install or build. Open `index.html` in a browser.

## Privacy

All calculations happen in your browser, and nothing you enter is sent anywhere. The calculator makes two kinds of network requests: it loads the IBM Plex Sans web font from Google Fonts, and it contacts Coinbase (or CoinGecko as a backup) only when you click **Use live price**. The daily brief loads `brief-data.json` from the same site and can refresh Bitcoin the same way. Those price requests carry no information from your inputs.

## Publish with GitHub Pages

1. Push `index.html` and `README.md` to a GitHub repository.
2. In the repository, go to **Settings → Pages**.
3. Under **Build and deployment**, choose **Deploy from a branch**, select `main` and the `/ (root)` folder, then save.
4. After a minute or two the site is live at `https://<your-username>.github.io/<repository-name>/`.

## Credits

Inspired by the [Bitcoin Retirement Calculator](https://github.com/bevstr/bitcoin-retirement-calculator), which works out how long a bitcoin stack lasts when you spend it down. This project runs a similar idea from the savings side, and its code is written separately.

The live price button was contributed by [@bevstr](https://github.com/bevstr) in pull request #1.

## License

Released under the [MIT License](LICENSE).

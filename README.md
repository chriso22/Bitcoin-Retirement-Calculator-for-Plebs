# Bitcoin Retirement Savings Calculator for Plebs

How much bitcoin do you need to retire on, and what can you withdraw each month? Enter the bitcoin you hold today, a monthly dollar amount you will buy until you retire, and how many years the money has to last. The calculator shows the monthly withdrawal that covers those years and whether any bitcoin is left over.

**Live:** add your GitHub Pages link here once it is published.

## What it models

Everything runs in monthly steps.

1. **Building the stack.** Each month until retirement you buy bitcoin with your monthly amount at that month's price, minus the trading fee. The price compounds by one month of your projected growth rate. You can raise the monthly buys with inflation.
2. **Retirement.** Each month you sell enough bitcoin to cover that month's withdrawal. You enter the withdrawal in today's dollars. The calculator inflates it to the year you retire, uses that larger figure as your first withdrawal, and keeps raising it with inflation so it holds its purchasing power.
3. **Tax and fees.** Tax applies only to the gain above your average cost basis, not to the whole sale. The cost basis blends what you already hold with what you buy along the way. The trading fee applies to both buys and sells.

### Inputs

| Input | Meaning |
| --- | --- |
| Bitcoin held today | The stack you start with |
| Price today | Typed in by hand (the page makes no network requests) |
| Buy each month | Dollars spent on bitcoin every month until you retire |
| Years of buying | How long until you retire |
| Raise monthly buys with inflation | Optional. Grows the monthly buy amount by the inflation rate |
| Years the money must last | Length of retirement |
| Monthly withdrawal to test | In today's dollars. Leave at 0 to test the maximum |
| Bitcoin growth per year | Projected annual growth. Negative values are allowed |
| Inflation per year | Applied to withdrawals (and to buys, if the option is on) |
| Cost basis of what you hold | Average price you paid for your existing bitcoin |
| Tax on gains | Applied to the gain above your cost basis |
| Trading fee | Percentage of each buy and each sale |

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

## Publish with GitHub Pages

1. Push `index.html` and `README.md` to a GitHub repository.
2. In the repository, go to **Settings → Pages**.
3. Under **Build and deployment**, choose **Deploy from a branch**, select `main` and the `/ (root)` folder, then save.
4. After a minute or two the site is live at `https://<your-username>.github.io/<repository-name>/`.

## Credits

Inspired by the [Bitcoin Retirement Calculator](https://github.com/bevstr/bitcoin-retirement-calculator), which works out how long a bitcoin stack lasts when you spend it down. This project runs a similar idea from the savings side, and its code is written separately.

## License

Released under the [MIT License](LICENSE).

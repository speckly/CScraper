# Kurokami

Kurokami is a web scraper and live monitoring tool for the marketplace Carousell. 
> [!NOTE]
> Support only for SG

> [!WARNING]
> Use this ethically as web scraping is heavily discouraged on this platform. Do not scrape more than needed.
> Once per 10 minutes is good enough

# Usage

For one time use
```
usage: kurokami.py [-h] [-i ITEM] [-p PAGE] [-o OUTPUT] [-t] [-s] [-c COMPARE]

options:
  -h, --help            show this help message and exit
  -i ITEM, --item ITEM  Name of the item to scrape
  -p PAGE, --page PAGE  Number of pages (approx 46 per page)
  -o OUTPUT, --output OUTPUT
                        CSV file to write out to
  -t, --test            For debugging of parsers which could break often due to the changing structure, using a snapshot 
                        of a bs4 object while overriding these flags with the respective values: -i shirakami fubuki -p 1
  -s, --serialize       For debugging of parsers which could break often due to the changing structure, the BS4 object is serialised for fast access, must not have -t
  -c COMPARE, --compare Name of a .csv file output from this program
```

For persistent monitoring, create a Discord [task](https://discordpy.readthedocs.io/en/stable/ext/tasks/index.html)

> [!WARNING]
> Running Kurokami currently blocks Discord API interactions when querying. This is because Kurokami is not asynchronous at the moment. Do not integrate Kurokami into your Discord bot if you require other features
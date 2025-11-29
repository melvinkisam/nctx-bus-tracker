"""Simple HTML fetcher using requests + BeautifulSoup.

Usage:
  python scraper.py            # fetch default NCTX stop page
  python scraper.py <url>      # fetch provided URL
"""
from __future__ import annotations
import argparse
import sys
from typing import Optional
import requests
from bs4 import BeautifulSoup


DEFAULT_URL = "https://www.nctx.co.uk/stops/3390BU05"
DIV_ID = "departure-board-wrapper"


# Fetch raw HTML and return as text
def get_html(url: str, timeout: int = 10) -> str:
	r = requests.get(url, timeout=timeout)
	r.raise_for_status() # Raise exception for HTTP errors
	
	return r.text


# Parse HTML with BeautifulSoup and return the soup object
def get_soup(url: str, timeout: int = 10) -> BeautifulSoup:
	html = get_html(url, timeout=timeout)
	
	return BeautifulSoup(html, "html.parser")


# Return the element with the given `id` from the page
def get_element_by_id(url: str, element_id: str = DIV_ID, timeout: int = 10) -> BeautifulSoup | None:
	soup = get_soup(url, timeout=timeout)
	el = soup.find(id=element_id)
	
	return el # Return the element or None if not found


def main(argv: list[str] | None = None) -> int:
	p = argparse.ArgumentParser(description="Fetch HTML and parse with BeautifulSoup")
	p.add_argument("url", nargs="?", default=DEFAULT_URL, help="URL to fetch")
	p.add_argument("--save", "-s", help="Save prettified HTML to file")
	p.add_argument("--id", "-i", dest="element_id", default=DIV_ID, help=f"Element id to extract (default: {DIV_ID}). If empty, prints whole page")
	args = p.parse_args(argv)

	try:
		if args.element_id:
			el = get_element_by_id(args.url, args.element_id)
			if el is None:
				print(f"Element with id '{args.element_id}' not found on {args.url}", file=sys.stderr)
				return 4
			pretty = el.prettify()
		else:
			soup = get_soup(args.url)
			pretty = soup.prettify()
	except requests.RequestException as exc:
		print(f"Failed to fetch {args.url}: {exc}", file=sys.stderr)
		return 2

	if args.save:
		try:
			with open(args.save, "w", encoding="utf-8") as fh:
				fh.write(pretty)
			print(f"Saved prettified HTML to {args.save}")
		except OSError as exc:
			print(f"Failed to write to {args.save}: {exc}", file=sys.stderr)
			return 3
	else:
		print(pretty)

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
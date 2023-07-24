import datetime
import logging
import os
import os.path
import sqlite3
from urllib.parse import parse_qs, urlparse

import atoma
import jinja2
import requests
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Email, HtmlContent, Mail, To

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)


class Storage:
    """
    A simple SQLite database to store articles.
    """

    def __init__(self, fname: str):
        self.conn = sqlite3.connect(fname)
        self._create_tables()

    def _create_tables(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY,
                title TEXT,
                link TEXT UNIQUE,
                published TEXT,
                summary TEXT
            )
            """
        )

    def store_article(self, item: atoma.rss.RSSItem) -> bool:
        """
        Store a singe article in the database.

        Returns True if the article was stored (new article),
        False if it was already in the database.
        """

        cur = self.conn.cursor()

        # Check if article is already in the database
        cur.execute(
            "SELECT id FROM articles WHERE link = ?",
            (item.link,),
        )
        row = cur.fetchone()
        if row:
            return False

        cur.execute(
            """
            INSERT INTO articles (title, link, published, summary)
            VALUES (?, ?, ?, ?)
            """,
            (item.title, item.link, item.pub_date, item.description),
        )
        self.conn.commit()
        return True


def get_ars_feed() -> list[atoma.rss.RSSItem]:
    """
    Fetch the Ars Technica RSS feed and return a list of RSSItem objects.
    """

    # Get the URL to the full feed from the environment
    url = os.environ.get("ARS_FEED_URL")

    # Fetch the feed
    response = requests.get(url)

    if not response.ok:
        log.error(f"Failed to fetch feed: {response.status_code}")
        return

    feed = atoma.parse_rss_bytes(response.content)
    for item in feed.items:
        parsed_link = urlparse(item.link)
        article_id = parse_qs(parsed_link.query)["p"][0]
        item.pdf_link = f"http://arstechnica.com?ARS_PDF={article_id}"
    return feed.items


def store_articles(
    storage: Storage,
    items: list[atoma.rss.RSSItem],
) -> list[atoma.rss.RSSItem]:
    """
    Store a list of RSSItem objects in the database.

    Returns a list of RSSItem objects that were stored (new articles).
    """
    new_items = []

    for item in items:
        is_new = storage.store_article(item)
        if is_new:
            new_items.append(item)

    return new_items


def prepare_daily_digest(items: list[atoma.rss.RSSItem]) -> str:
    """
    Prepare the daily digest email with the new articles.
    """
    template_path = os.path.join(os.path.dirname(__file__), "template.html")
    template = jinja2.Template(open(template_path).read())
    return template.render(
        items=items,
        date=datetime.date.today().strftime("%A, %B %d, %Y"),
    )


def send_daily_digest(content: str) -> None:
    """
    Send a daily digest email with the new articles using Sendgrid.
    """

    # Fetch the Sendgrid API key from the environment
    api_key = os.environ.get("SENDGRID_API_KEY")

    from_email = os.environ.get("FROM_EMAIL")
    recipient = os.environ.get("RECIPIENT_EMAIL")

    # Initialize the Sendgrid client
    sg = SendGridAPIClient(api_key)

    # Send the email
    message = Mail(
        Email(from_email),
        To(recipient),
        "Ars Technica Daily Digest",
        HtmlContent(content),
    )
    response = sg.send(message)
    if response.status_code != 202:
        log.error(f"Failed to send email: {response.status_code}")


def run_daily_digest():
    """
    Run the daily digest process.
    """

    load_dotenv()
    db_path = os.environ.get("DB_PATH")
    storage = Storage(db_path)
    items = get_ars_feed()
    new_items = store_articles(storage, items)
    if new_items:
        content = prepare_daily_digest(new_items)
        send_daily_digest(content)


if __name__ == "__main__":
    run_daily_digest()

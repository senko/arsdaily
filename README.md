# ArsDaily

A digest newsletter for ArsTechnica articles. Can be run daily (hence the name),
weekly, or at any other interval.

The newsletter uses a subscriber-specific RSS feed to fetch the articles and
creates an email with the articles in HTML format. The email is sent to the
recipient address using Sendgrid or Amazon SES.

For each article, only the title, summary, link to the web and link to the
subscriber PDF are included.

ArsDaily is **NOT** affiliated with or endorsed by ArsTechnica.

## Installation

ArsDaily requires Python 3.9+.

Clone the repository:

    git clone git@github.com:senko/arsdaily.git
    cd arsdaily/

Set up and activate a new Python virtual environment:

    python -m venv .venv
    source .venv/bin/activate

Install the dependencies:

    pip install -r requirements.txt

Configure the environment variables:

    cp env.sample .env
    vim .env

Run the script:

    python src/digest.py

## License

ArsDaily is licensed under the MIT license. See the `LICENSE` file for details.

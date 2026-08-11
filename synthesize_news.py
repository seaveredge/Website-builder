import re
from datetime import date
from html import escape

from main import html_template, get_file_content

import markdown

def get_raw_news():
    news_lines = get_file_content("news.md").splitlines()
    return news_lines

def inline_markdown(text: str) -> str:
    """
    Convert Markdown intended for a single line into HTML.

    Supports normal Markdown links, that should link to the outside world, and internal links, indicated with 
    ```md
        [label](url){int}.
    ```
    """

    # Temporarily protect our custom links so that Markdown doesn't
    # process them before we can add target="_blank".

    links = []

    def save_link(match):
        label = match.group(1)
        url = match.group(2)
        modifier = match.group(3)

        placeholder = f"$$INTLINK{len(links)}$$"
        links.append((label, url, modifier))
        return placeholder
    
    # Match:
    #   [text](url)
    #   [text](url){int}
    # So substitute all links with placeholders, and save the label and url and link type for later.
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)(?:\{(int)\})?', save_link, text)

    # Let Python-Markdown handle the normal Markdown.
    html = markdown.markdown(text)

    # Remove the <p> wrapper because this is inline Markdown.
    if html.startswith("<p>") and html.endswith("</p>"):
        html = html[3:-4]

    # Replace our protected links.
    for i, (label, url, modifier) in enumerate(links):
        placeholder = f"$$INTLINK{i}$$"

        # Allow Markdown inside the link text.
        label_html = markdown.markdown(label)

        if label_html.startswith("<p>") and label_html.endswith("</p>"):
            label_html = label_html[3:-4]

        if modifier == "int":
            link_html = (
                f'<a href="{escape(url, quote=True)}">'
                f'{label_html}'
                f'</a>'
            )
        else:
            link_html = (
                f'<a href="{escape(url, quote=True)}" '
                f'target="_blank" rel="noopener">'
                f'{label_html}'
                f'</a>'
            )
        

        html = html.replace(placeholder, link_html)

    return html


def parse_line(line: str) -> tuple[date, str]:
    """Parse 'DATE | text' into a date and text."""

    line = line.strip()

    if not line or line.startswith("#"):
        raise ValueError("Empty/comment line")

    try:
        date_text, content = line.split("|", 1)
    except ValueError:
        raise ValueError(
            f"Expected 'DATE | TEXT', got: {line!r}"
        )

    entry_date = date_text.strip()[1:].strip() # remove the leading '-'
    if len(entry_date) != 10:
        raise ValueError(
            f"Expected date in YYYY-MM-DD format, got: {entry_date!r}"
        )
    
    return entry_date.strip(), content.strip()


def generate_dl(
    lines: list[str],
    limit: int | None = None,
    newest_first: bool = False,
) -> str:
    """Generate the HTML <section><dl>...</dl></section>."""

    entries = []

    for line_number, line in enumerate(lines, start=1):
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        try:
            entry_date, text = parse_line(line)
        except ValueError as e:
            raise ValueError(
                f"Error on line {line_number}: {e}"
            ) from e

        entries.append((entry_date, text))

    if newest_first:
        entries.sort(reverse=True)
    else:
        entries.sort()

    if limit is not None:
        entries = entries[:limit]

    output = [
        "<section>",
        "  <dl>",
    ]

    for entry_date, text in entries:
        html = inline_markdown(text)

        output.append(
            f"    <dt>{entry_date}</dt>"
        )
        output.append(
            f"    <dd>{html}</dd>"
        )

    output.extend([
        "  </dl>",
        "</section>",
    ])

    return "\n".join(output)

if __name__ == "__main__":
    news_lines = get_raw_news()
    dl_html = generate_dl(news_lines, limit=None, newest_first=True)
    print(dl_html)
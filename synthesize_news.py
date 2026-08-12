import re
from datetime import date
from html import escape

from main import html_template, get_file_content

import markdown


# An entry always starts with:
# - DD-MM-YYYY | Some text
ENTRY_RE = re.compile(
    r"^-\s*(\d{2}-\d{2}-\d{4})\s*\|\s*(.*)$"
)

# Custom items such as:
# $$SPECIAL1$$
# $$SPECIAL42$$
ITEM_RE = re.compile(r"\$\$SPECIAL(\w+)\$\$")

def get_raw_news():
    news_lines = get_file_content("news.md").splitlines()
    return news_lines


def parse_entries(lines: list[str]) -> list[dict]:
    """
    Parse the source file into entries.

    A new entry starts with:
        - DD-MM-YYYY | text

    All following lines belong to that entry until another entry
    starts.
    """

    entries = []
    current = None

    for line_number, line in enumerate(lines, start=1):
        line = line.rstrip()

        match = ENTRY_RE.match(line)

        if match:
            # Save the previous entry.
            if current is not None:
                entries.append(current)

            current = {
                "date": match.group(1),
                "lines": [match.group(2)],
                "line_number": line_number,
            }

        elif current is not None:
            # Everything after an entry belongs to that entry.
            current["lines"].append(line)

        elif line.strip():
            raise ValueError(
                f"Line {line_number} appears before the first entry: "
                f"{line!r}"
            )

    # Don't forget the final entry.
    if current is not None:
        entries.append(current)

    return entries


def convert_custom_items(
    html: str,
    items: dict[str, str],
) -> str:
    """
    Replace $$SPECIALx$$ markers with custom HTML.

    Example:

        $$SPECIAL1$$

    with:

        {
            "SPECIAL1": '<figure>...</figure>'
        }
    """

    def replace(match):
        identifier = match.group(1)
        key = f"SPECIAL{identifier}"

        if key not in items:
            raise ValueError(
                f"Unknown custom item: $${key}$$"
            )

        return items[key]

    return ITEM_RE.sub(replace, html)


def markdown_to_html(
    text: str,
    items: dict[str, str],
) -> str:
    """
    Convert Markdown to HTML.

    Custom $$SPECIALx$$ markers are protected before Markdown
    conversion and replaced afterwards.
    """

    # Markdown shouldn't try to interpret our custom markers.
    # Replace them with safe placeholders first.
    # # custom_items = []

    # # def save_item(match):
    # #     identifier = match.group(1)
    # #     key = f"SPECIAL{identifier}"

    # #     if key not in items:
    # #         raise ValueError(
    # #             f"Unknown custom item: $${key}$$"
    # #         )

    # #     placeholder = f"___CUSTOM_ITEM_{len(custom_items)}___"
    # #     custom_items.append((placeholder, items[key]))

    # #     return placeholder
    
    # # text = ITEM_RE.sub(save_item, text)

    # # Convert Markdown.
    # html = markdown.markdown(
    #     text,
    #     extensions=[
    #         "nl2br",
    #     ],
    # )

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
    md = markdown.Markdown(extensions=["nl2br"])
    html = md.convert(text)

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

    # Put the custom HTML back.
    for identifier in items:
        html = html.replace(f'$${identifier}$$', items[identifier])

    return html


def generate_dl(
    entries: list[dict],
    items: dict[str, str],
    limit: int | None = None,
    old_new: bool = False,
) -> str:
    """
    Generate the final HTML <section><dl>...</dl></section>.
    """


    if limit is not None:
        if old_new: # true = new
            entries = entries[:limit]
        else: # false = old
            entries = entries[limit:]

    output = [
        "<dl>",
    ]

    for entry in entries:
        text = "\n   ".join(entry["lines"])

        html = markdown_to_html(
            text,
            items,
        )

        output.append(
            f"  <dt>{entry['date']}</dt><dd>{html}</dd>"
        )

    output.extend([
        "</dl>",
    ])

    return "\n".join(output)


def generate_from_file(
    items: dict[str, str],
    limit: int | None = None,

) -> str:
    """
    Read the Markdown source file and generate the HTML.
    """

    lines = get_raw_news()

    entries = parse_entries(lines)

    # robustness value for limit
    if limit is not None:
        limit = max(1, limit)  # Ensure at least one entry is included.
        limit = min(limit, len(entries))  # Don't exceed the number of entries.
    else:
        limit = len(entries)  # Include all entries if no limit is specified.
    last_date = entries[limit-1]['date']
    new_news = generate_dl(entries, items=items, limit=limit, old_new=True)
    old_news = generate_dl(entries, items=items, limit=limit, old_new=False)
    return new_news, old_news, last_date

# END OF MARKDOWN FUNCTIONS


if __name__ == "__main__":
    SPECIAL_ITEMS = {
        "SPECIAL1": "<figure><img src=\"https://assets.w3.tue.nl/w/fileadmin/_processed_/7/6/csm_130525%20Verhoek%20Promotie_8e1c9e104f.jpg\" alt=\"Defense\" style=\"width:60%; border-radius: 5%;\"></figure>",
    }
    NUMBER_OF_NEWS_ITEMS = 20

    # Generate HTML for new and old news items:
    html_new, html_old, last_date = generate_from_file(
            items=SPECIAL_ITEMS,
            limit=NUMBER_OF_NEWS_ITEMS,
        )

    # generate html templates and fill with old or new news!
    newnews = html_template("articles/research/t_newnews.html")
    newnews.replace_text('NEWNEWS', html_new)
    newnews.replace_text('DATELAST', last_date)

    oldnews = html_template("articles/research/t_oldnews.html")
    oldnews.replace_text('OLDNEWS', html_old)
    oldnews.replace_text('DATELAST', last_date)

    # save generated files
    newnews.save_contents('articles/research','g_news.html')
    oldnews.save_contents('articles/research/blog','g_oldnews.html')

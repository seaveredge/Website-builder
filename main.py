import re
import os
os.chdir(os.path.dirname(__file__))
from datetime import datetime

def iseven(n): return n % 2 == 0

def get_file_content(filename):
    # Read the HTML file
    with open(filename, 'r', encoding='utf-8') as f:
        file_contents = f.read()
    return file_contents


def extract_identifiers(html_content):
    # first check if there is an even number of patterns:
    count = html_content.count("$$$")
    if not iseven(count): raise ValueError("Not even number of identifiers in the file...")

    # now extract the identifiers
    pattern = r'\$\$\$(.*?)\$\$\$'
    # return all matches of the pattern in the file content
    return re.findall(pattern, html_content, re.DOTALL)


class html_template:
    def __init__(self, filename):
        self.filename = filename
        self.content = get_file_content(filename)
        self.identifiers = extract_identifiers(self.content)
        # print('Identifiers in ' + filename + ':')
        # print(self.identifiers)

    def replace_text(self, identifier, newtext):
        if identifier not in self.identifiers: raise ValueError('Identifier not in file!!')
        self.content = self.content.replace("$$$" + identifier + "$$$", newtext)

    def return_content(self):
        self.cleanup_content()
        if not extract_identifiers(self.content): return self.content
        else: raise ValueError("Not all the identifiers are covered...")

    def save_contents(self, folder_path="output", file_name="index.html"):
        if folder_path is None: folder_path="output"
        if file_name   is None: file_name="index.html"
        # check if folder actually exists...
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        # Create the file path
        file_path = os.path.join(folder_path, file_name)
        # cleanup file
        self.cleanup_content()
        # Write the modified HTML content to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.content)

    def cleanup_content(self):
        """
        cleanup the html content (removing comments and white lines)
        """
        # Remove all HTML comments from the content
        pattern = r'<!--(.*?)-->'
        self.content = re.sub(pattern, '', self.content)

        # Remove leading and trailing whitespace lines
        lines = self.content.split('\n')
        while lines and not lines[0].strip(): lines.pop(0) # leading
        while lines and not lines[-1].strip(): lines.pop() # trailing
        self.content = '\n'.join(lines) + '\n' # save back to self.content


class Header(html_template):
    def __init__(self, title):
        super().__init__("blocks/header.html")
        self.replace_text("TITLE", title)
        if "ome" in title:
            self.replace_text("STYLE1", "bold")
        elif "search" in title:
            self.replace_text("STYLE2", "bold")
        elif "sonal" in title:
            self.replace_text("STYLE3", "bold")
        self.identifiers = extract_identifiers(self.content)
        for _id in self.identifiers:
            if "STYLE" in _id:
                self.replace_text(_id, "normal")
        self.items = ""

    def add_item_to_list(self, name, tag):
        # If the tag starts with a "#", this means an escape character and tag[1:] is used
        TAG = tag[1:] if tag[0] == "#" else "#" + tag
        newitem = "<span><a href=\"" + TAG + "\" style=\"font-style: italic;\">" + name + "</a></span>\n"
        self.items = self.items + newitem

    def write_items(self):
        self.replace_text("ITEMS", self.items[:-1]) # -1 to remove white space


class Footer(html_template):
    def __init__(self, date_time_str=None):
        super().__init__("blocks/footer.html")
        # if len(self.identifiers) > 0: raise ValueError("Footer contains identifiers, while we did not expect them...") # Does not have identifiers, so a bit redundant for being a class...
        if date_time_str is None:
            date_time_str = datetime.now().strftime("%Y-%m-%d")
        self.replace_text("DATETIME", date_time_str)



def make_index_file(Body_obj, output_folder=None, file_name=None, done_date_time=None):
    # Assumption is that Body_obj is "complete"
    html_file = html_template("blocks/main.html")
    Header_obj = Header(Body_obj.title)
    Body_obj.add_all_articles()
    Footer_obj = Footer(done_date_time)

    # Build the header;
    #   Body_obj.header_items is a list of 2-element tuple,
    #   where item[0] = name and item[1] = tag.
    for item in Body_obj.header_items:
        Header_obj.add_item_to_list(item[0], item[1])
    Header_obj.write_items()

    # Replace identifiers
    html_file.replace_text("TITLE", Body_obj.title + " page of Chris Verhoek")
    html_file.replace_text("DESCRIPTION", "Professional and personal webpage of Chris Verhoek - " + Body_obj.title + " page")
    html_file.replace_text("HEADER", Header_obj.return_content())
    html_file.replace_text("BODY", Body_obj.return_content())
    html_file.replace_text("FOOTER", Footer_obj.return_content())


    html_file.save_contents(folder_path=output_folder, file_name=file_name)




class Body(html_template):
    def __init__(self, title):
        self.title = title
        self.header_items = []
        super().__init__("articles/" + self.title.lower() + "/main.html")
        self.articles = ""

    def add_html_article(self,filename,name,tag=None):
        if tag is None: tag = name.lower()
        article_content = "<article id=\"" + tag + "\">\n"
        f =  html_template("articles/" + self.title.lower() + "/" + filename)
        article_content = article_content + f.return_content()
        article_content = article_content + "\n</article>\n"
        self.articles = self.articles + article_content
        self.header_items.append((name,tag))

    def add_markdown_article(self,filename,name,tag):
        pass # TODO: make this function

    def add_all_articles(self):
        self.replace_text("ARTICLES", self.articles)

    def add_header_item(self,name, tag):
        self.header_items.append((name, tag))

    def reset_body(self):
        self.content = "$$$ARTICLES$$$"


if __name__ == '__main__':
    exec(open("synthesize_refs.py").read())
    # Home page
    home = Body('Home')
    home.add_html_article("aboutme.html", "About me", tag="aboutme")
    home.add_html_article("background.html", "Academic background", tag="background")
    make_index_file(home, output_folder="./../Homepage")

    #===================================================================================================================
    # Research page
    research = Body('Research')
    research.add_html_article("news.html", "News")
    research.add_html_article("blog.html", "Blogs")
    research.add_html_article("publications.html", "Publications")
    make_index_file(research, output_folder="./../SD-research")

    # separate pages
    cdc2021page = Body('Research')
    cdc2021page.reset_body() # required to make an empty page
    cdc2021page.add_html_article("blog/cdc2021.html","Back to blogs","#https://research.chrisverhoek.com/#blogs")
    make_index_file(cdc2021page, output_folder="./../SD-research/content",file_name="cdc2021.html", done_date_time="2021-09-14")

    slidespage = Body('Research')
    slidespage.reset_body()  # required to make an empty page
    slidespage.add_html_article("blog/slides.html", "Back to blogs", "#https://research.chrisverhoek.com/#blogs")
    make_index_file(slidespage, output_folder="./../SD-research/content", file_name="slides.html")

    softwarepage = Body('Research')
    softwarepage.reset_body()  # required to make an empty page
    softwarepage.add_html_article("blog/software.html", "Back to blogs", "#https://research.chrisverhoek.com/#blogs")
    make_index_file(softwarepage, output_folder="./../SD-research/content", file_name="software.html")

    #===================================================================================================================
    # Personal page
    personal = Body('Personal')
    personal.add_html_article("prev_gc.html","Hiking in Gran Canaria","grancanaria")
    personal.add_html_article("prev_web.html", "Building this website", "website")
    personal.add_html_article("prev_ice.html", "Hiking in Iceland", "iceland")
    make_index_file(personal, output_folder="./../SD-personal")

    grancanaria = Body('Personal')
    grancanaria.reset_body()  # required to make an empty page
    grancanaria.add_header_item("Back to personal page", "#https://personal.chrisverhoek.com/") # tag with escape character
    grancanaria.add_html_article("blog/grancanaria.html", "Hiking in Gran Canaria", "grancanaria")
    make_index_file(grancanaria, output_folder="./../SD-personal/content", file_name="grancanaria.html")

    iceland = Body('Personal')
    iceland.reset_body()  # required to make an empty page
    iceland.add_header_item("Back to personal page", "#https://personal.chrisverhoek.com/") # tag with escape character
    iceland.add_html_article("blog/iceland.html", "Hiking in Iceland", "iceland")
    make_index_file(iceland, output_folder="./../SD-personal/content", file_name="iceland.html", done_date_time="2024-06-18")

    website = Body('Personal')
    website.reset_body()  # required to make an empty page
    website.add_header_item("Back to personal page", "#https://personal.chrisverhoek.com/") # tag with escape character
    website.add_html_article("blog/website.html", "Building this website", "website")
    make_index_file(website, output_folder="./../SD-personal/content", file_name="website.html", done_date_time="2025-10-09")



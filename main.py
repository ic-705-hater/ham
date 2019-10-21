from bs4 import BeautifulSoup as bs4
import requests, time, easygui, re
from slackclient import SlackClient
from datetime import datetime, date
from requests_html import HTMLSession
# PS: The IC-705 is stupid
"""
line 16 - slack client api if you want CL ads to post to a slack channel
line 20 - your CL city in URL
line 62 - CL keywords to search (just broard ham phrases right now)
line 64 - product for gigaparts/ham radio outlet/QTH
"""

posted = []
# Slack connection
slack_client = SlackClient('XXXX-000000000000-xxxxxx0xxxx00xxxxxxxx00x')

# searches CL for keyword and posts to Slack
def cl(keyword):
    url_base = ('https://YOUR-CITY.craigslist.org/search/sss')
    params = dict(query=keyword, sort='date')
    rsp = requests.get(url_base, params=params, verify=False)
    html = bs4(rsp.text, 'html.parser')
    shit = []
    shit = html.find_all('p', attrs={'class': 'result-info'})
    for s in shit:
        link = s.find('a', attrs={'class': 'result-title'})
        text = link.text
        link = link.get('href')
        if link not in posted:
            price = s.find('span', attrs={'class': 'result-price'})
            if price is None:
                continue
            elif '$0' in price.text:
                continue
            else:
                price = int(price.text.replace('$', ''))
                if price in range(5, 700):
                    date = s.find('time', attrs={'class': 'result-date'})
                    if (datetime.now() - datetime.strptime(date['datetime'], '%Y-%m-%d %H:%M')).days <= 2:
                        desc = text + "\n" + str(price) + ", " + date.text + "\n" + link
                        slack_client.api_call('chat.postMessage', channel='land', text=desc, as_user='true:')
                        posted.append(link)
                        print(text)

def ham_radio_outlet(link):
    session = HTMLSession()
    resp = session.get(link, verify=False)
    resp.html.render(sleep=1, keep_page=True)
    soup = bs4(resp.html.html, "lxml")
    title = soup.find('h1', 'dtitles').text
    desc = soup.find('h2', 'dtitles2').text
    condition = soup.find('p', 'open').text
    price = soup.find('p', 'addtoCart').text
    try:
        easygui.msgbox(msg=desc + '\n' + condition + '\n' + price + '\n' + link, title=title)
    except Exception as e:
        print(e)
    time.sleep(2)

#craigslist keywords
keywords = ['swr', 'vertex', 'kenwood microphone', 'radio equipment', 'radio antenna', 'PL-259', 'icom', 'yaesu', 'amature radio', 'Amateur radio', 'ham radio', 'transciever', 'radio microphone', 'morse code', 'ssb', 'telegraph key', 'antenna tower']
ham_outlet_links = ['https://www.hamradio.com/feed_open.cfm', 'https://www.hamradio.com/feed_used.cfm']
my_product = 'IC-7300'
ic_shown = []

while True:
    try:
        for keyword in keywords:
            cl(keyword)
    except Exception as e:
        print(e)
    for ic in ham_outlet_links:
        url_base = (ic)
        rsp = requests.get(url_base, verify=False)
        html = bs4(rsp.content, 'html.parser')
        items = html.find_all('item')
        for h in items:
            if my_product in str(h):
                link = re.search(r'https://www.hamradio.com/[\w./?=\d-]+', str(h)).group()
                if link not in ic_shown:
                    ic_shown.append(link)
                    time.sleep(5)
                    ham_radio_outlet(link)

        time.sleep(2)
    page = requests.get('https://www.gigaparts.com/catalogsearch/advanced/result/?name=' + my_product + '&sku=&description=&short_description=&price%5Bfrom%5D=400&price%5Bto%5D=930', verify=False)
    soup = bs4(page.content, 'html.parser')
    products = soup.find_all('div', 'product-item-details')
    for product in products:
        try:
            name = product.find('a').text.rstrip().lstrip() + '\n' + product.find('a')['href'] + '\n' + product.find('span', 'price').text
            if product.find('a')['href'] not in ic_shown:
                easygui.msgbox(msg=name, title='Giga Parts')
                ic_shown.append(product.find('a')['href'])
        except Exception as e:
            pass
    page = requests.get('https://swap.qth.com/search-results.php?keywords=' + my_product + '&fieldtosearch=TitleOrDesc', verify=False)
    soup = bs4(page.content, 'html.parser')
    tables = soup.find_all('table')
    m_text = ''
    for table in tables:
        xx = table.find_all('dl')
        for x in xx:
            m_text = m_text + x.text
    z = m_text.split('\n\n')
    products = []
    for a in z:
        try:
            posted_date = a.split('\n')[-2].split('Submitted on ')[1].split(' by Call')[0]
            if (date.today() - datetime.strptime(posted_date, '%m/%d/%y').date()).days < 10:
                listing = title = a.split('\n')[0] + '\n' + a.split('\n')[1:-1][0] + '\n' + 'https://swap.qth.com/view_ad.php?counter=' + a.split('Listing #')[1].split(' -  ')[0] + '\n\n'
                if listing not in ic_shown:
                    products.append(listing)
                    ic_shown.append(listing)
        except Exception as e:
            pass
    easygui.textbox("QTH Findings: ", 'QTH', products)
    time.sleep(60 * 60)

import requests
from bs4 import BeautifulSoup
import json

from typing import List, Tuple

domain = 'http://mysql.taobao.org'


def load_mapping() -> (dict, dict):
    with open('./mapping.json', 'r') as f:
        data = json.load(f)
        return data['main_category'], data['article_mapping']


def parse_homepage():
    category_mapping, identity_mapping = load_mapping()
    url = domain + '/monthly/'
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find('ul', class_='posts')
    posts_dict = dict()
    for e in posts.find_all('li'):
        a = e.find_next('a', href=True)
        parse_one_monthly(a['href'], posts_dict, category_mapping, identity_mapping)
    write_to_markdown(posts_dict)


def parse_one_monthly(href: str, post_dict: dict, category_mapping: dict, identity_mapping: dict):
    url = domain + href
    monthly = href[9:]
    print('parse ' + url)
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    lists = soup.find_all('a', attrs={'class': 'main'}, href=True)
    for article in lists:
        identity = article['href'][9:-1]
        article_url = domain + article['href']
        content = article.text
        # print(content)
        a = content.split('·', maxsplit=2)
        main_category = '其他'
        category = ''
        title = None

        # 解析目录，分类，标题等
        if len(a) == 3:
            main_category = a[0].strip()
            category = a[1].strip()
            title = a[2].strip()
        elif len(a) == 1:
            title = a[0].strip()
        elif len(a) == 2:
            main_category = a[0].strip()
            title = a[1].strip()
        if main_category in category_mapping:
            main_category = category_mapping[main_category]

        # 对于部分信息缺失的，从mapping中获取
        if identity in identity_mapping:
            temp = identity_mapping[identity].get('main_category')
            if temp is not None:
                main_category = temp
            temp = identity_mapping[identity].get('category')
            if temp is not None:
                category = temp
            temp = identity_mapping[identity].get('title')
            if temp is not None:
                title = temp
        category_dict = post_dict.setdefault(main_category, dict())
        list_titles = category_dict.setdefault(category, list())
        list_titles.append([title, article_url, monthly])


def write_to_markdown(post_dict: dict):
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write('# 阿里云数据库内核月报分类整理\n\n')
        for main_category in sorted(post_dict.keys(), key=lambda item: (item == '', item)):
            f.write('* [{}](#{})\n'.format(main_category, main_category))
        for main_category, category_dict in sorted(post_dict.items(), key=lambda item: (item[0] == '', item[0])):
            f.write('\n')
            f.write('# {}\n'.format(main_category))
            f.write('|{}|{}|{}|\n'.format('分类', '时间', '标题'))
            f.write('|{}|{}|{}|\n'.format('---', '---', '---'))
            list_articles: List[Tuple[str, str, str]]
            for category, list_articles in sorted(category_dict.items(), key=lambda item: (item[0] == '', item[0])):
                for (title, url, monthly) in sorted(list_articles, key=lambda item: (item[2] == '', item[2]),
                                                    reverse=False):
                    f.write('|{}|{}|[{}]({})\n'.format(category, monthly, title, url))


if __name__ == '__main__':
    parse_homepage()

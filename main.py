import os
import json
import requests
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def _get_soup(url):
    """
    Отримує об'єкт BeautifulSoup для заданого URL.

    url (str): URL для отримання.
    """
    response = requests.get(url)
    return BeautifulSoup(response.content, 'html.parser')


class SiteParser:
    def __init__(self, url):
        self.url = url

    def _absolute_url(self, url):
        """
        Конвертує відносний URL у абсолютний URL, використовуючи базовий URL сайту.

        url (str): URL для конвертації.
        """
        return urljoin(self.url, url)


class PhotoParser(SiteParser):
    def __init__(self, url, save_folder):
        super().__init__(url)
        self._save_folder = save_folder

    @property
    def save_folder(self):
        return self._save_folder

    @save_folder.setter
    def save_folder(self, value):
        self._save_folder = value

    def _save_photo(self, url):
        """
        Зберігає фото з заданого URL у вказану теку.

        url (str): URL фото.
        """
        if url.startswith('http://') or url.startswith('https://'):
            response = requests.get(url)
            filename = hashlib.sha1(url.encode()).hexdigest() + ".jpg"
            with open(os.path.join(self.save_folder, filename), 'wb') as f:
                f.write(response.content)
        else:
            print(f"URL {url} має непідтримуваний протокол і не буде збережено.")

    def parse_photos(self):
        """
        Аналізує HTML-контент сайту для пошуку та збереження всіх фото.

        list: Список URL-адрес збережених фото.
        """
        soup = _get_soup(self.url)
        photo_urls = []

        # Створення теки для збереження фото, якщо вона не існує
        os.makedirs(self.save_folder, exist_ok=True)

        # Пошук всіх тегів img з атрибутом src
        img_tags = soup.find_all('img', src=True)
        for img_tag in img_tags:
            photo_url = self._absolute_url(img_tag['src'])
            photo_urls.append(photo_url)
            # Збереження фото в теку
            self._save_photo(photo_url)

        return photo_urls


def save_text_to_file(text, filename):
    """
    Зберігає заданий текст у файл з вказаним ім'ям.

    text (str): Текст для збереження.
    filename (str): Ім'я файлу для збереження.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)


class TextParser(SiteParser):
    def __init__(self, url):
        super().__init__(url)
        self._filename = 'text_output.txt'

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = value

    def parse_text(self):
        """
        Аналізує HTML-контент сайту для видобування та збереження тексту.

        str: Ім'я файлу, де збережений текст.
        """
        response = requests.get(self.url)
        response.encoding = 'utf-8'  # Встановлення правильної кодування для тексту
        soup = BeautifulSoup(response.text, 'html.parser')

        # Отримання тексту з тегів p, заголовків і таблиць
        text = ""
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'div']):
            tag_text = ' '.join(tag.stripped_strings)
            if tag_text:  # Перевірка, чи містить тег текст
                if tag.name == 'table':
                    # Додавання тексту з комірок таблиці
                    for row in tag.find_all('tr'):
                        for cell in row.find_all('td'):
                            cell_text = ' '.join(cell.stripped_strings)
                            if cell_text:
                                text += f"Тег: {tag.name}, Текст: {cell_text.replace('вот', '')}\n"
                else:
                    text += f"Тег: {tag.name}, Текст: {tag_text.replace('вот', '')}\n"

        # Додавання тексту з тега title
        title_tag = soup.find('title')
        if title_tag:
            title_text = ' '.join(title_tag.stripped_strings)
            if title_text:  # Перевірка, чи містить тег текст
                text += f"Тег: title, Текст: {title_text.replace('вот', '')}\n"

        # Збереження тексту у текстовий файл
        filename = self.filename
        save_text_to_file(text, filename)

        return filename


def save_links_to_file(links, filename):
    """
    Зберігає заданий список посилань у файл з вказаним ім'ям.

    links (list): Список URL-адрес для збереження.
    filename (str): Ім'я файлу для збереження.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        for link in links:
            f.write(link + '\n')


class LinkParser(SiteParser):

    def __init__(self, url):
        super().__init__(url)
        self._filename = 'urls_output.txt'

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = value

    def parse_links(self):
        """
        Аналізує HTML-контент сайту для пошуку та збереження всіх посилань.

        str: Ім'я файлу, де збережені посилання.
        """
        soup = _get_soup(self.url)
        links = []

        # Пошук всіх тегів a (посилання) з атрибутом href
        a_tags = soup.find_all('a', href=True)
        for a_tag in a_tags:
            link = self._absolute_url(a_tag['href'])
            links.append(link)

        # Збереження посилань у текстовий файл
        filename = 'urls_output.txt'
        save_links_to_file(links, filename)

        return filename


if __name__ == "__main__":
    # Введення URL від користувача
    url = input("Введіть URL веб-сайту для аналізу: ")

    # Введення типу даних для аналізу
    data_type = input("Що ви хочете аналізувати (photo, txt, urls, all): ")

    # Створення екземплярів класів в залежності від пибраного типу даних
    parsed_data = {}
    if data_type == "all":
        photo_parser = PhotoParser(url, "photos")
        text_parser = TextParser(url)
        link_parser = LinkParser(url)

        parsed_data["photos"] = photo_parser.parse_photos()
        parsed_data["text"] = text_parser.parse_text()
        parsed_data["urls"] = link_parser.parse_links()
    elif data_type == "photo":
        parser = PhotoParser(url, "photos")
        parsed_data["photos"] = parser.parse_photos()
    elif data_type == "txt":
        parser = TextParser(url)
        parsed_data["text"] = parser.parse_text()
    elif data_type == "urls":
        parser = LinkParser(url)
        parsed_data["urls"] = parser.parse_links()
    else:
        print("Непідтримуваний тип даних")
        exit()

    # Збереження даних у файли JSON
    for key, value in parsed_data.items():
        output_file = f"{key}.json"
        with open(output_file, 'w') as f:
            json.dump(value, f)
        print(f"Дані успішно збережено у файл {output_file}")

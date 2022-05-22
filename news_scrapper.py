"""News Scrapper"""
import json
import random as rd
import re
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timedelta
from time import sleep
from typing import Dict
from typing import List

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import exceptions as selenium_exceptions
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from tqdm import tqdm
from unidecode import unidecode

from config import Config


class BotDetectedException(Exception):
    """The browser has blocked the scrapper"""


class MaxTrialsReachedException(Exception):
    pass


@dataclass
class DailyNews:
    urls: list[str]
    # Maps a keyword to the number of times it was matched
    keyword_match_counter: dict[str, int] = field(default_factory=dict[str, int])


class NewsScrapper:
    def __init__(self, headless: bool = True) -> None:

        self.headless = headless
        self._init_browser()

    def _init_browser(self) -> None:

        chrome_options = Options()

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-popup-blocking")
        if self.headless:
            chrome_options.add_argument("--headless")

        self.browser = webdriver.Chrome(Config.CHROME_DRIVER_LOCAL_PATH, options=chrome_options)  # type: ignore
        self.browser.set_page_load_timeout(Config.MAX_TIMEOUT_SECS)

    def scrap_news(
        self,
        search_keywords: List[str],
        content_keywords: List[str],
        from_dt: datetime,
        to_dt: datetime,
        data_folder_path: str,
        optional_search_keywords: List[str] = [],
        max_pages_by_search: int = 3,
    ) -> None:
        """
        Scrap news on the internet trying to match keywords
        Saves a csv report of the results

        Args:
            search_keywords (List[str]): Must words used to search with the browser.
            content_keywords (List[str]): Words to match in the websites found by the browser.
            from_dt (datetime): From when the search begins.
            to_dt (datetime): To when the search goes.
            data_folder_path (str): Folder to save the reports.
            optional_search_keywords (List[str], optional): Optional words used to search with the browser. Defaults to [].
            max_pages_by_search (int, optional): Defaults to 3.
        """

        df: pd.DataFrame = pd.DataFrame([], columns=["date", "url quantity"] + content_keywords)
        for day_delay in tqdm(range((to_dt - from_dt).days + 1), colour="blue", desc="DATES"):

            current_date = from_dt + timedelta(day_delay)
            try:
                daily_news: DailyNews = self._scrap_news_by_day(
                    search_keywords=search_keywords,
                    optional_search_keywords=optional_search_keywords,
                    content_keywords=content_keywords,
                    max_pages_by_search=max_pages_by_search,
                    date_filter=current_date,
                )
            except Exception:
                # We were able to properly process the news until this date
                to_dt = current_date - timedelta(1)
                break

            sleep(rd.randint(7, 15))

            df = df.append(
                {
                    "date": current_date,
                    "url quantity": len(daily_news.urls),
                    "urls": daily_news.urls,
                    **daily_news.keyword_match_counter,
                },
                ignore_index=True,
            )

        self._save_report(
            from_dt=from_dt,
            to_dt=to_dt,
            data_folder_path=data_folder_path,
            search_keywords=search_keywords,
            optional_search_keywords=optional_search_keywords,
            content_keywords=content_keywords,
            report_df=df,
        )
        self.browser.quit()

    def _scrap_news_by_day(
        self,
        search_keywords: List[str],
        content_keywords: List[str],
        date_filter: datetime,
        optional_search_keywords: List[str] = [],
        max_pages_by_search: int = 3,
    ) -> DailyNews:

        urls: List[str] = self._try_get_urls(
            search_keywords=search_keywords,
            optional_search_keywords=optional_search_keywords,
            date_filter=date_filter,
            max_pages=max_pages_by_search,
        )
        keyword_match_counter: Dict[str, int] = {k: 0 for k in content_keywords}
        for url in tqdm(
            urls,
            colour="white",
            desc="URLS",
            leave=False,  # Erase progress bar after it finishes
        ):

            keyword_matches = self._find_matches(url=url, content_keywords=content_keywords)
            keyword_match_counter = {k: keyword_match_counter.get(k, 0) + int(v) for k, v in keyword_matches.items()}

        return DailyNews(urls=urls, keyword_match_counter=keyword_match_counter)

    def _find_matches(
        self,
        url: str,
        content_keywords: List[str],
    ) -> Dict[str, bool]:

        text = self._extract_text(url=url)
        keyword_matches: Dict[str, bool] = {}
        for content_keyword in content_keywords:
            keyword_matches[content_keyword] = bool(
                re.search(
                    content_keyword,
                    unidecode(text),
                    re.IGNORECASE,
                ),
            )

        return keyword_matches

    def _try_get_urls(
        self,
        search_keywords: List[str],
        date_filter: datetime,
        max_pages: int,
        optional_search_keywords: List[str] = [],
        max_tries: int = 3,
    ) -> List[str]:

        self._search(
            search_keywords=search_keywords,
            optional_search_keywords=optional_search_keywords,
            from_dt=date_filter,
            to_dt=date_filter,
        )

        counter: int = 0
        while True:
            if counter > max_tries:
                raise MaxTrialsReachedException("Party's over")
            counter += 1

            try:
                return self._get_urls(max_pages=max_pages)
            except Exception:
                pass

            self._restart_search(
                search_keywords=search_keywords,
                date_filter=date_filter,
            )

    def _restart_search(
        self,
        search_keywords: List[str],
        date_filter: datetime,
    ) -> None:

        self._init_browser()
        sleep(rd.randint(5, 10))
        self._search(
            search_keywords=search_keywords,
            from_dt=date_filter,
            to_dt=date_filter,
        )
        sleep(rd.randint(7, 12))

    def _search(
        self,
        search_keywords: List[str],
        from_dt: datetime,
        to_dt: datetime,
        optional_search_keywords: List[str] = [],
    ) -> None:

        self.browser.get(
            Config.GOOGLE_SEARCH_URL.format(
                keywords=self._format_search_keywords(search_keywords, optional_search_keywords),
                from_date=from_dt.strftime(Config.GOOGLE_DATE_FORMAT),
                to_date=to_dt.strftime(Config.GOOGLE_DATE_FORMAT),
            ),
        )

    def _get_urls(self, max_pages) -> List[str]:

        urls: List[str] = [
            url.get_attribute("href") for url in self.browser.find_elements(by=By.XPATH, value=Config.WEBSITE_URL_XPATH)
        ]
        for i in range(2, max_pages + 1):

            if "unusual traffic" in self.browser.page_source:
                raise BotDetectedException("Party's over")

            sleep(rd.randint(3, 7))

            try:
                page_index_button = self.browser.find_element(
                    by=By.XPATH,
                    value=Config.PAGE_INDEX_BUTTON_URL_XPATH.format(page_number=i),
                )
            except selenium_exceptions.NoSuchElementException:
                break

            page_index_button.click()
            urls += [
                url.get_attribute("href")
                for url in self.browser.find_elements(
                    by=By.XPATH,
                    value=Config.WEBSITE_URL_XPATH,
                )
            ]

        return urls

    @staticmethod
    def _save_report(
        from_dt: datetime,
        to_dt: datetime,
        data_folder_path: str,
        search_keywords: List[str],
        content_keywords: List[str],
        report_df: pd.DataFrame,
        optional_search_keywords: List[str] = [],
    ) -> None:

        file_path: str = f"{data_folder_path}/{from_dt.strftime('%d-%m-%Y')}_{to_dt.strftime('%d-%m-%Y')}_{datetime.now().timestamp()}"
        report_df.to_csv(
            file_path + ".csv",
            index=False,
        )

        # Save metadata
        with open(file_path + ".txt", "w") as f:
            json.dump(
                {
                    "search keywords": search_keywords,
                    "optional search keywords": optional_search_keywords,
                    "content keywords": content_keywords,
                },
                f,
            )

    @staticmethod
    def _format_search_keywords(
        search_keywords: List[str],
        optional_search_keywords: List[str] = [],
    ) -> str:
        return "+".join([f'"{sk}"' for sk in search_keywords]) + "+" + "+".join(optional_search_keywords)

    @staticmethod
    def _extract_text(url: str) -> str:

        try:
            resp = requests.get(url)
        except Exception:
            html_page: bytes = b""
        else:
            html_page: bytes = resp.content if resp.status_code in range(200, 300) else b""

        soup = BeautifulSoup(html_page, "html.parser")
        return " ".join([str(t) for t in soup.find_all(text=True) if t.parent.name not in Config.TAG_BLACKLIST])

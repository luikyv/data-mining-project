import warnings
from datetime import datetime
from typing import List

from config import Config
from news_scraper import NewsScraper

waterlogging_locals: List[str] = [
    "rua geraldo barbosa",
    "avenida dos expedicionarios",
    "rua joao carvalho",
    "avenida conselheiro lafaiete",
    "tunel da avenida rogaciano leite",
    "avenida washington soares",
    "avenida alberto sa",
    "avenida heraclito graca",
    "avenida jose bastos",
    "avenida desembargador moreira",
]
search_keywords: List[str] = ["fortaleza", "alagamento", "chuva"]
# optional_search_keywords: List[str] = ["enchente"]

if __name__ == "__main__":

    warnings.filterwarnings("ignore")

    news_scrapper = NewsScraper(
        headless=False,
    )
    news_scrapper.scrap_news(
        search_keywords=search_keywords,
        content_keywords=waterlogging_locals,
        from_dt=datetime(day=31, month=12, year=2021),
        to_dt=datetime(day=31, month=12, year=2021),
        data_folder_path=Config.LOCAL_DATA_FOLDER_PATH,
        max_pages_by_search=3,
    )

"""Configurations"""
import pathlib
from typing import List


class Config:
    CHROME_DRIVER_LOCAL_PATH: str = f"{pathlib.Path(__file__).parent}/chromedriver"
    LOCAL_DATA_FOLDER_PATH: str = f"{pathlib.Path(__file__).parent}/data"
    GOOGLE_DATE_FORMAT: str = "%m/%d/%Y"
    MAX_TIMEOUT_SECS: int = 20
    TAG_BLACKLIST: List[str] = [
        "[document]",
        "noscript",
        "html",
        "meta",
        "head'",
        "input",
        "script",
    ]

    #################### URLS ####################
    GOOGLE_SEARCH_URL: str = "https://www.google.com/search?q={keywords}&tbs=cdr:1,cd_min:{from_date},cd_max:{to_date}"

    #################### XPaths ####################
    WEBSITE_URL_XPATH: str = "//a[contains(@href, 'https')][not(contains(@href, 'google'))][not(contains(@href, 'search'))][not(contains(@href, 'pdf'))][not(contains(@href, 'txt'))][not(contains(@href, 'png'))]"
    PAGE_INDEX_BUTTON_URL_XPATH: str = "//a[@class='fl' and normalize-space()='{page_number}']"

import json
import logging
from datetime import datetime
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup as bs

logger = logging.getLogger(__name__)


HEADERS: Dict[str, str] = {
    "accept": "*/*",
    "user-agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/85.0.4183.83 Safari/537.36"
    ),
}


def read_json_file(filename: str) -> dict:
    with open(filename, "r") as f:
        data: dict = json.load(f)
    return data


def get_csrf_token() -> Optional[str]:
    with requests.Session() as session:
        response: requests.Response = session.get(
            url="https://zhambyltipo.kz/kk/site/login", headers=HEADERS
        )
        logger.info("Scraping csrf token")
        soup = bs(response.content, "lxml")
        csrf: Optional[str] = soup.find("meta", attrs={"name": "csrf-token"}).get(
            "content", None
        )

    return csrf


def get_today_date():
    return datetime.today().strftime("%d.%m.%Y")

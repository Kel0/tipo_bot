import json
import logging
import re
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup as bs

from settings import BASE_DIR

from .utils import HEADERS, get_csrf_token, get_today_date

logger = logging.getLogger(__name__)
site_prefix = "https://zhambyltipo.kz"


class Auth:
    """
    Authenticate methods class
    """

    def __init__(self) -> None:
        self.csrf_token = get_csrf_token()
        self.headers = HEADERS
        self.login_url = "https://zhambyltipo.kz/kk/site/login"
        self.logout_url = "https://zhambyltipo.kz/site/logout"

    def login(self, username: str, password: str) -> Optional[requests.Session]:
        """
        Login to account
        :param username: Username
        :param password: Password
        :return: Logged in requests.Session object
        """
        data: Dict[str, Optional[str]] = {
            "_csrf": self.csrf_token,
            "LoginForm[username]": username,
            "LoginForm[password]": password,
            "login-button": "",
        }

        with requests.Session() as session:
            login_response: requests.Response = session.post(
                url=self.login_url, headers=self.headers, data=data
            )  # login post request
            logger.info("Logging in...")

            if login_response.status_code == 200:
                return session
            else:
                logger.warning(f"Login failed | {login_response.status_code}")
                return None

    def logout(self) -> bool:
        """
        Logout from accout
        :return: if response.status_code is 200 returns True else False
        """
        data: Dict[str, Optional[str]] = {
            "_csrf": self.csrf_token,
        }

        with requests.Session() as session:
            response: requests.Response = session.post(
                url=self.logout_url, headers=self.headers, data=data
            )  # logout post request
            logger.info("Logging out...")

            if response.status_code == 200:
                return True
            else:
                logger.warning(f"Logout failed | {response.status_code}")
                return False


class SiteEvents:
    def __init__(self, login_session: requests.Session):
        self.login_session = login_session
        self.home_works_url = "https://zhambyltipo.kz/admin/student/homeworks"
        self.class_works_url = "https://zhambyltipo.kz/admin/student/classworks"

    @staticmethod
    def write_schedule(data: List[Dict[str, str]]) -> None:
        """
        Write schedule to json file
        :param data: List of dicts which contains info about time and subject's remote lesson link.
            {"time": "09:00", "link": "some_link"}.
        """
        with open("schedule.json", "w+") as f:
            f.truncate()
            json.dump(data, f, ensure_ascii=False, indent=4)

    def get_todays_schedule(self) -> Optional[List[Dict[str, str]]]:
        """
        Get today's schedule
        :return objects: List of dicts which contains info about time and subject's remote lesson link.
            {"time": "09:00", "link": "some_link"}.
        """
        today_date = get_today_date()
        response: requests.Response = self.login_session.get(
            url="https://zhambyltipo.kz/admin/student/schedules", headers=HEADERS
        )

        soup = bs(response.content, "lxml")
        schedules = soup.find("table", attrs={"id": "schedules"})

        schedules_dates = schedules.find("thead").find_all("th")  # Get topics
        schedules_objects = schedules.find("tbody").find_all("tr")  # Get contents

        for key, schedules_date in enumerate(schedules_dates):
            date_span = schedules_date.find("span", attrs={"class": "text-muted"})
            if date_span is None:  # skip if date is None
                continue

            date: str = date_span.text.strip()
            subjects: List[Dict[str, str]] = []

            if str(date) != str(today_date):
                continue

            for subject in schedules_objects:
                temp_dict = {}
                div_lists = ["name", "subject", "lecture", "format"]

                try:
                    if subject.find_all("td")[key].find("div"):
                        temp_dict["time"] = [
                            time
                            for time in subject.find_all("td")[0].text.split(
                                " "
                            )  # split time text 09:00-09:35
                            if len(time) > 4
                        ][0]

                        count = 1
                        for dict_key, _div in zip(
                            div_lists, subject.find_all("td")[key].find_all("div")
                        ):
                            text: str = (
                                subject.find_all("td")[key]
                                .find_all("div")[count]
                                .text.strip()
                            )
                            if "Дистанционное обучение" in text:
                                _text = re.match(
                                    r"Дистанционное обучение\s+(\D+)\s+", text
                                )
                                if _text is not None:
                                    text = _text.group(1)

                            temp_dict[dict_key] = text
                            count += 1

                        _link = subject.find_all("td")[key].find("div").find("a")
                        temp_dict["link"] = None

                        if _link is not None:
                            temp_dict["link"] = site_prefix + _link.get(
                                "href", "no_href"
                            )

                        subjects.append(temp_dict)
                except AttributeError:
                    continue

            return subjects
        return None

    def scrape_subjects(self, type_: str) -> List[Dict[str, str]]:
        link: str = ""
        links = []

        if type_ == "home":
            link = self.home_works_url
        elif type_ == "class":
            link = self.class_works_url

        response = self.login_session.get(url=link, headers=HEADERS)
        soup = bs(response.content, "lxml")

        list_group_flush = soup.find(
            "div", attrs={"class": "list-group-flush"}
        ).find_all("a")

        for a_tag in list_group_flush:
            text_subject = re.sub(
                r"\d+", "", a_tag.find("h5", attrs={"class": "text-dark"}).text
            ).strip()
            href = a_tag.get("href")

            links.append({"subject": text_subject, "link": href})

        return links

    def scrape_class_works_of_subject(
        self, link: str
    ) -> Optional[Dict[str, Optional[str]]]:
        response = self.login_session.get(url=f"{site_prefix}{link}", headers=HEADERS)
        soup = bs(response.content, "lxml")

        table = soup.find("table", attrs={"class": "table-hover"}).find("tbody")
        trs = table.find_all("tr")

        class_works: Dict[str, Optional[str]] = {
            "type": "file",
            "file": None,
            "filename": None,
        }
        subject_info_keys = (
            "id",
            "subject",
            "group",
            "teacher",
            "material",
            "date",
            "created_at",
            "updated_at",
        )

        if len(trs) == 1:
            return None

        current_tr = trs[0]
        tds = current_tr.find_all("td")
        info_link = tds[-1].find("a").get("href")

        info_response = self.login_session.get(
            url=f"{site_prefix}{info_link}", headers=HEADERS
        )
        info_soup = bs(info_response.content, "lxml")

        card = info_soup.find("div", attrs={"class": "card"})
        sub_cards = card.find_all("div", attrs={"class": "card-body"})

        class_works.update({
            "desc": "\n".join([element.text for element in sub_cards[-1].find_all("p")]),
        })

        info_table = info_soup.find("table", attrs={"id": "w0"})
        info_trs = info_table.find_all("tr")

        for title, tr in zip(subject_info_keys, info_trs):
            content = tr.find("td")

            title_text = title
            content_text = content.text.strip()

            if title == "material":
                content_link = content.find("a")

                if content_link is not None:
                    content_link_href = content_link.get("href")
                    if len(re.findall(r"(dpaste|paste)", content_link_href, re.I)) > 0:
                        class_works["type"] = "paste"
                        class_works["filename"] = content_link_href
                        class_works["file"] = content_link_href
                        continue

                    content_response = self.login_session.get(
                        url=f"{site_prefix}{content_link.get('href')}", headers=HEADERS
                    )
                    filename = content_link.get("download")
                    filepath = f"{BASE_DIR}/storage/{filename}"
                    with open(filepath, "wb") as f:
                        f.write(content_response.content)

                    title_text = "file"
                    content_text = filepath
                    class_works["filename"] = filename

            class_works.update({title_text: content_text})

        return class_works

    def scrape_home_works_of_subject(
        self, link: str
    ) -> Optional[Dict[str, Optional[str]]]:
        response = self.login_session.get(url=f"{site_prefix}{link}", headers=HEADERS)
        soup = bs(response.content, "lxml")

        table = soup.find("table", attrs={"class": "table-hover"}).find("tbody")
        trs = table.find_all("tr")

        home_works = {}
        current_tr = trs[0]

        data_key = current_tr.get("data-key")
        tds = current_tr.find_all("td")

        if len(tds) == 1:
            return None

        filename = None
        file_path = None
        hw_link = soup.find("div", attrs={"id": f"modal-files-{data_key}"})

        files_match = re.match(r"\D+\(([\d]{1,})\)$", tds[5].text.strip())
        if files_match is None:
            return None

        files_count = int(files_match.group(1))

        if hw_link is not None and files_count > 0:
            _body = hw_link.find("div", attrs={"class": "modal-body"})
            extension = (
                hw_link.find("tbody").find_all("td")[1].text.strip().split(".")[-1]
            )  # get extension of file

            modal_link = site_prefix + _body.find("a").get("href")
            download_response = self.login_session.get(url=modal_link, headers=HEADERS)

            filename = f"{tds[2].text.strip()[:15]}.{extension}"
            file_path = f"{BASE_DIR}/storage/{filename}"
            with open(file_path, "wb") as f:
                f.write(download_response.content)

        home_works.update(
            {
                "data_key": data_key,
                "name": tds[1].text.strip(),
                "desc": tds[2].text.strip(),
                "deadline": tds[3].text.strip(),
                "teacher": tds[4].text.strip(),
                "file": file_path,
                "filename": filename,
                "created_at": tds[6].text.strip(),
            }
        )

        return home_works

    def go_to_lesson(self) -> list:
        schedule = self.get_todays_schedule()
        visited_lessons = []
        if schedule is None:
            raise ValueError("No schedule")

        for subject in schedule:
            if subject["link"] is not None:
                self.login_session.get(url=subject["link"], headers=HEADERS)
                visited_lessons.append(subject)
                logger.info(f"Requested {subject['link']}")

        return visited_lessons

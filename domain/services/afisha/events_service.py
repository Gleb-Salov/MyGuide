import httpx
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
import logging
import re
from urllib.parse import urlparse


class EventParser:
    def __init__(self, base_url: str = "https://afisha.relax.by/", timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(20)


    async def fetch_with_semaphore(self, link: str, client: httpx.AsyncClient) -> Dict[str, Any]:
        async with self.semaphore:
            return await self.fetch_event_details(link, client)

    async def fetch_html(self, url: str, retries: int = 5) -> Optional[str]:
        for attempt in range(1, retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.text
            except (httpx.HTTPError, httpx.ReadTimeout):
                if attempt == retries:
                    raise
                await asyncio.sleep(2)
        return None

    def get_parent_name_from_url(self) -> str:
        path = urlparse(self.base_url).path
        parts = path.strip("/").split("/")

        category_map = {
            "kino": "Movies",
            "festivali": "Festivals",
        }
        if parts:
            key = parts[0].lower()
            return category_map.get(key, "Unknown")
        return "Unknown"

    @staticmethod
    def clean_text(text: str, *, filter_digits: bool = False) -> Optional[str]:
        if not text:
            return None
        text = text.replace('\u200e', '')
        text = re.sub(r"[\s-]*\d{4,}$", "", text).strip()
        if filter_digits:
            digits = sum(c.isdigit() for c in text)
            if digits > 5 and re.fullmatch(r"[\d\s+\-()]*", text):
                return None
        return text or None

    @staticmethod
    def normalize_description(desc: Optional[str]) -> Optional[str]:
        if not desc:
            return None
        return desc.strip().lower().replace('\n', ' ').replace('\r', '')

    @staticmethod
    def parse_datetime_from_str(date_str: str) -> Optional[datetime]:
        try:
            date_part, time_part = date_str.split()
            for sep in ['/', '.', '-', '_']:
                time_part = time_part.replace(sep, ':')
            dt_str = f"{date_part} {time_part}"
            return datetime.strptime(dt_str, "%m/%d/%Y %H:%M")
        except ValueError as e:
            logging.warning(f"Failed to parse date_str='{date_str}': {e}")
            return None

    async def fetch_event_details(self, link: str, client: httpx.AsyncClient) -> Dict[str, Any]:
        try:
            resp = await client.get(link)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            desc_tag = soup.select_one("div.b-afisha_cinema_description_text")
            description = desc_tag.text.strip() if desc_tag else None
            normalized_description = self.normalize_description(description)

            interests = list(filter(None, (
                self.clean_text(a_tag.text.strip(), filter_digits=True)
                for a_tag in soup.select("div.b-afisha_cinema_description_table a") if a_tag.text.strip()
            )))

            date_locations = []
            time_tags = soup.select("a.schedule__seance-time")

            for time_tag in time_tags:
                date_raw = time_tag.get("data-date-format")
                dt = self.parse_datetime_from_str(date_raw) if date_raw else None

                schedule_item = time_tag.find_parent("div", class_="schedule__item")
                if not schedule_item:
                    schedule_wrap = time_tag.find_parent("div", class_="schedule__seance-wrap")
                    schedule_seance = schedule_wrap.find_parent("div",
                                                                class_="schedule__seance") if schedule_wrap else None
                    schedule_item = schedule_seance or schedule_wrap

                location = None
                if schedule_item:
                    place_tag = schedule_item.select_one("div.schedule__place a.schedule__place-link")
                    address_tag = schedule_item.select_one("div.schedule__place span.text-black-light")
                    if place_tag:
                        place_name = place_tag.text.strip()
                        address = address_tag.text.strip() if address_tag else None
                        location = f"{place_name}, {address}" if address else place_name

                if dt:
                    location = (location or time_tag.get("data-category") or "Unknown location").strip()
                    normalized_location = self.clean_text(location)
                    date_locations.append({"date": dt, "location": normalized_location})

            return {
                "description": normalized_description,
                "interests": interests,
                "date_locations": date_locations
            }
        except (httpx.HTTPError, httpx.RequestError, httpx.TimeoutException, AttributeError) as e:
            logging.warning(f"Failed to fetch details for {link}: {e}")
            raise

    async def retry_request(self,retry_tasks: list,
                            retry_events: list,
                            client: httpx.AsyncClient,
                            max_retries: int = 3) -> List[Any]:
        filtered_events = []
        for attempt in range(1, max_retries + 1):
            retry_results = await asyncio.gather(*retry_tasks, return_exceptions=True)
            retry_tasks = []
            retry_events_next = []
            for event, details in zip(retry_events, retry_results):
                if isinstance(details, Exception):
                    logging.warning(f"Retry failed for '{event['title']}': {repr(details)}")
                    if attempt < max_retries:
                        retry_tasks.append(self.fetch_with_semaphore(event["link"], client))
                        retry_events_next.append(event)
                else:
                    event.update(details)
                    filtered_events.append(event)
            retry_events = retry_events_next
            if not retry_events:
                break
        return filtered_events

    async def parse_events_from_html(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        event_items = soup.select("div.b-afisha-layout_strap--item")

        events = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            tasks = []
            for item in event_items:
                title_tag = item.select_one("a.b-afisha_blocks-strap_item_lnk_txt")
                if not title_tag:
                    continue

                title = title_tag.text.strip()
                link = title_tag.get("href")
                if not title or not link:
                    continue

                img_tag = item.select_one("img")
                img_url = img_tag.get("src") or img_tag.get("data-src") if img_tag else None

                tasks.append(self.fetch_with_semaphore(link, client))

                events.append({
                    "title": title,
                    "link": link,
                    "img": img_url,
                })

            details_list = await asyncio.gather(*tasks, return_exceptions=True)

            filtered_events = []
            retry_tasks = []
            retry_events = []
            for event, details in zip(events, details_list):
                if isinstance(details, Exception):
                    logging.warning(f"Skipping event '{event['title']}' due to error: {repr(details)}")
                    retry_tasks.append(self.fetch_with_semaphore(event["link"], client))
                    retry_events.append(event)
                else:
                    event.update(details)
                    filtered_events.append(event)
            if retry_tasks:
                retry = await self.retry_request(retry_tasks, retry_events, client)
                filtered_events.extend(retry)

            filtered_events = [event for event in filtered_events if event.get("date_locations")]
            return filtered_events

    async def parse(self) -> List[Dict[str, Any]]:
        main_html = await self.fetch_html(self.base_url)
        if not main_html:
            return []
        return await self.parse_events_from_html(main_html)

if __name__ == "__main__":
    async def main():
        parser = EventParser()
        events = await parser.parse()
        for event in events:
            print(event)

    asyncio.run(main())

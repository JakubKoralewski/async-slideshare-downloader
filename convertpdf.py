#!/usr/bin/env python
# -*- coding: utf-8 -*-
# https://askubuntu.com/a/1004158
import sys
import img2pdf
from pathlib import Path
import asyncio
import aiohttp

from bs4 import BeautifulSoup  # python3

CURRENT = Path(__file__).parent
OUTPUT = CURRENT / "pdf_images"


async def fetch_image(session, url, index):
    print(f"fetching {url}")
    async with session.get(url) as response:
        bytes = await response.read()
        return index, bytes


async def download_images(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, features="html.parser")
            images = soup.findAll('img', {'class': 'slide_image'})
            tasks = []
            slide_folder = OUTPUT / url.split('/')[-1]
            slides_output = slide_folder / "slides"

            for i, image in enumerate(images):
                image_file = slides_output / f"{i}.jpg"
                if image_file.exists():
                    continue
                image_url = image.get('data-full').split('?')[0]
                task = asyncio.ensure_future(fetch_image(session, image_url, i))
                tasks.append(task)

            for coro in asyncio.as_completed(tasks):
                i, image = await coro
                if not slides_output.exists():
                    slides_output.mkdir(parents=True)
                image_file = slides_output / f"{i}.jpg"
                print(f"Writing image of slide number {i} to {image_file.relative_to(CURRENT)}")
                image_file.write_bytes(image)
            pdf_file = slide_folder / (slide_folder.name + ".pdf")
            convert_pdf(slides_output, pdf_file)


def convert_pdf(img_dir: Path, pdf_file: Path):
    f = [x for x in img_dir.iterdir()]
    f.sort(key=lambda x: x.name)
    f = [x.open('rb') for x in f]
    print(f)

    pdf_bytes = img2pdf.convert(f, dpi=300, x=None, y=None)
    pdf_file.write_bytes(pdf_bytes)
    [x.close() for x in f]


if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = " ".join(sys.argv[1:])
    else:
        url = input('Slideshare URL: ').strip()
    if (url.startswith("'") and url.endswith("'")) or (url.startswith('"') and url.endswith('"')):
        url = url[1:-1]
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    loop = asyncio.get_event_loop()
    loop.run_until_complete(download_images(url))

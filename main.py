import json
import logging
import os
import random
import shutil
import string
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import IO, Optional
from zipfile import ZipFile

from asgiref.sync import sync_to_async
from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from pyppeteer import launch
from pyppeteer.browser import Browser
from pyppeteer.page import Page

router = APIRouter()

p = Path(os.environ.get("PYPPETEER_HOME", "/tmp/PYPPETEER_HOME"))
p.mkdir(exist_ok=True)
BROWSER: Optional[Browser] = None

from pyppeteer.chromium_downloader import DOWNLOADS_FOLDER, REVISION, check_chromium, download_chromium  # noqa

if not check_chromium():
    download_chromium()

for child in Path(DOWNLOADS_FOLDER).iterdir():
    if not child.name == REVISION:
        folder = str(child.resolve())
        logging.info("Found old chrome revision deleting: {}".format(folder))
        shutil.rmtree(folder)


async def get_blank_page() -> Page:
    global BROWSER
    if not BROWSER:
        try:
            BROWSER = await launch(headless=True, args=[            '--no-sandbox',
                '--single-process',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-zygote'])
        except Exception:
            from pyppeteer.launcher import Launcher
            logging.error(' '.join(Launcher().cmd))
            raise
    return await BROWSER.newPage()


async def html_to_pdf(url: str, out_path: str, options: dict = None) -> None:
    start = datetime.now()
    logging.info("Starting HTML to pdf")
    page = await get_blank_page()
    await page.goto(url)

    await page.pdf(
        path=out_path,
        # pass in as dict instead of unpacking with ** so that explicit kwargs override instead of clash
        options=options,
    )
    await page.close()
    logging.info(f"Generated PDF in {datetime.now() - start} from {url}")
    return


@router.get("/", response_class=HTMLResponse)
async def get_webpage() -> str:
    return """
            <html>
            <body>
                <p>
                POST to this url or add a ?url= param
                </p>
                <form action="" method="post"  enctype="multipart/form-data">
                    <ul>
                        <li>
                            <input type="file" name="file" accept="zip">
                            <label for="file">zip containing HTML entrypoint, css, images etc</file>
                        </li>
                        <li>
                            <input type="text" name="entrypoint" value="index.html">
                            <label for="entrypoint">file to render within zip file</label>
                        </li>
                        <li>
                            <input type="textarea" name="options_json" value="{}">
                            <label for="options_json">options_json, as per
                            <a href="https://miyakogi.github.io/pyppeteer/reference.html#pyppeteer.page.Page.pdf"
                                        target="_blank">pyppeteer PDF options</a></label>
                        </li>
                        <li>
                            <input type="submit" value="Upload">
                        </li>
                    </ul>
                </form>
            </body>
            </html>
            """


@sync_to_async
def unzip(memzip: IO, folder: str) -> None:
    myzip = ZipFile(memzip)
    myzip.extractall(folder)


def delete_files_after_request(folder_path: str) -> None:
    shutil.rmtree(folder_path, ignore_errors=True)


@router.post("/")
async def process_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),  # noqa
    options_json: str = Form("{}"),  # noqa
    entrypoint: str = Form("index.html"),  # noqa
) -> FileResponse:
    pdf_options = json.loads(options_json)
    folder_name = "".join(random.choice(string.ascii_letters) for _ in range(10))
    folder_path = f"/tmp/htmltopdf/{folder_name}"
    os.makedirs(folder_path, exist_ok=True)
    background_tasks.add_task(delete_files_after_request, folder_path)

    memzip = BytesIO()
    memzip.write(await file.read())  # type: ignore
    await unzip(memzip, folder_path)  # noqa

    url = f"file://{folder_path}/{entrypoint}"
    logging.info(f"Rendering {url}")
    pdf_path = f"{folder_path}/res.pdf"
    await html_to_pdf(url, pdf_path, pdf_options)

    return FileResponse(pdf_path, filename="file.pdf")

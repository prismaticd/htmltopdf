import os
from pathlib import Path
import shutil
import string
import random
from flask import g


os.environ["PYPPETEER_HOME"] = os.path.join(os.path.dirname(__file__), "/tmp/PYPPETEER_HOME")

# local_chromium = Path(os.path.dirname(__file__)) / "local-chromium"
# # local_chromium.mkdir(exist_ok=True)
#
p = Path(os.environ['PYPPETEER_HOME'])
p.mkdir(exist_ok=True)
#
# l = p / "local-chromium"
# l.symlink_to(local_chromium)

from pyppeteer.chromium_downloader import download_chromium, check_chromium, DOWNLOADS_FOLDER, REVISION

if not check_chromium():
    download_chromium()

for child in Path(DOWNLOADS_FOLDER).iterdir():
    if not child.name == REVISION:
        folder = str(child.resolve())
        print("Found old chrome revision deleting: {}".format(folder))
        shutil.rmtree(folder)


import asyncio
import json
import os
from datetime import datetime
from zipfile import ZipFile

from flask import send_file
from pyppeteer import launch
from werkzeug.utils import secure_filename

BROWSER = None


async def get_blank_page():
    global BROWSER
    if not BROWSER:
        BROWSER = await launch(args=["--no-sandbox"])
    return await BROWSER.newPage()


async def html_to_pdf(url, out_path, options=None):
    start = datetime.now()
    print("Starting HTML to pdf")
    page = await get_blank_page()
    await page.goto(url)

    await page.pdf(
        path=out_path,
        # pass in as dict instead of unpacking with ** so that explicit kwargs override instead of clash
        options=options,
    )
    await page.close()
    print(f"Generated PDF in {datetime.now() - start} from {url}")
    return


def main(request):
    # request_json = request.get_json()
    url = request.args.get("url")
    if not url and request.method == "GET":
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
                        <a href="https://miyakogi.github.io/pyppeteer/reference.html#pyppeteer.page.Page.pdf" target="_blank">pyppeteer PDF options</a></label>
                    </li>
                    <li>
                        <input type="submit" value="Upload">
                    </li>
                </ul>
            </form>
        </body>
        </html>
        """

    pdf_options = {}

    if request.method == "POST":
        if "file" not in request.files:
            print(request.files)
            return "ERROR: No file part"
        file = request.files["file"]
        if file.filename == "":
            return "ERROR: No selected file"
        if file:
            pdf_options = json.loads(request.form.get("options_json", "{}"))
            entrypoint = request.form.get("entrypoint", "index.html")

            filename = secure_filename(file.filename)
            folder_name = "".join(random.choice(string.ascii_letters) for _ in range(10))
            g.folder_path = f"/tmp/htmltopdf/{folder_name}"
            os.makedirs(g.folder_path, exist_ok=True)

            zip_location = os.path.join(g.folder_path, filename)
            file.save(zip_location)

            with ZipFile(zip_location, "r") as myzip:
                myzip.extractall(g.folder_path)

            url = f"file://{g.folder_path}/{entrypoint}"
            print(url)

        print(f"Rendering {url}")
        pdf_path = f"{g.folder_path}/res.pdf"
        asyncio.get_event_loop().run_until_complete(html_to_pdf(url, pdf_path, pdf_options))

        return send_file(pdf_path, attachment_filename="file.pdf")

    return "Error"



import os
import shutil
from main import main
# This is only for local test, Google cloud functions are not calling this part

from flask import Flask
from flask import request, g


# Need to Wrap  the app to set the loop and to inject request in the function
def main_wrapper():
    #asyncio.set_event_loop(asyncio.new_event_loop())
    try:
        res = main(request)
        return res
    except Exception as e:
        print(e)
    return None


local_app = Flask(__name__)
local_app.add_url_rule("/", "main", view_func=main_wrapper, methods=("GET", "POST"))
# app.run(debug=False, use_reloader=False)


@local_app.teardown_request
def teardown_request(exception):
    folder_path = g.get("folder_path", None)
    if folder_path:
        print(f"Cleaning {folder_path}")
        shutil.rmtree(folder_path, ignore_errors=True)


if __name__ == "__main__":
    # Use simple WSGI server (single threaded to avoid signal issue)
    from wsgiref.simple_server import make_server

    port = int(os.environ.get("HEADLESS_CHROME_PORT", 8009))
    web = make_server("", port, local_app)
    print(f"Serving on port {port}...")
    web.serve_forever()

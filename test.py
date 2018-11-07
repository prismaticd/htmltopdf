import requests
from multiprocessing.dummy import Pool as ThreadPool

URL_TO_TEST = "http://127.0.0.1:8009"


def hammer_it():
    with open('test_http/index.html.zip', 'rb') as f:
        files = {'file': f}
        res = requests.post(URL_TO_TEST, files=files)
        print(res.status_code)


pool = ThreadPool(8)

for _ in range(1, 100):
    pool.apply(hammer_it)




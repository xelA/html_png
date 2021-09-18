import requests
import threading


def worker(num):
    print(f"Worker START: {num}")
    requests.post("http://localhost:8080", json={
        "html": "<h1>AlexFlipnote</h1>"
    })
    print(f"Worker END: {num}")
    return


threads = []
for g in range(100):
    t = threading.Thread(target=worker, args=(g,))
    threads.append(t)
    t.start()

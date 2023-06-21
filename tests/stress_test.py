import requests
import threading


def worker(num):
    print(f"Worker START: {num}")
    r = requests.post(
        "http://127.0.0.1:8575",
        json={"html": f"<h1>AlexFlipnote {num}</h1>"}
    )

    with open(f"./dump/{num}.png", "wb") as f:
        f.write(r.content)

    print(f"Worker END: {num}")
    return


threads = []
for g in range(100):
    t = threading.Thread(target=worker, args=(g,))
    threads.append(t)
    t.start()

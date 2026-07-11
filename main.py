import threading
from crawling import service
from db import get_collection



from pymongo.errors import BulkWriteError

def crawling(group_id, count=50):
    try:
        print(f"{threading.current_thread().name} 開始")

        results = service(group_id, count=count)
        collection = get_collection("posts")

        try:
            collection.insert_many(results, ordered=False)
        except BulkWriteError:
            pass
    finally:
        print(f"{threading.current_thread().name} 已結束")

group_list = [
    "628916884757960",
    "1867100664072671",
    "1243250902386508",
]

def crawling_threadpool(groups):
    threads = []

    for group in groups:
        t = threading.Thread(
            target=crawling,
            args=(group,)
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

if "__main__" == __name__:
    crawling_threadpool(group_list)


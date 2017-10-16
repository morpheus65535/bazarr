import datetime, threading, time

def foo():
    next_call = time.time()
    while True:
        print datetime.datetime.now()
        next_call = next_call+1;
        time.sleep(next_call - time.time())

timerThread = threading.Thread(target=foo)
timerThread.daemon = True
timerThread.start()

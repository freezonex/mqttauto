import threading
import time

import yibu
import mqttsend

def run_script1():
    mqttsend.main()

def run_script2():
    yibu.main()

if __name__ == '__main__':
    # Creating threads
    thread1 = threading.Thread(target=run_script1)
    thread2 = threading.Thread(target=run_script2)

    # Starting threads
    thread1.start()
    time.sleep(3)
    thread2.start()

    # Joining threads to ensure they both complete
    thread1.join()
    thread2.join()

    print("Both scripts have completed execution.")

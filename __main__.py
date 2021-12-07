#!/usr/sbin/python3

import argparse
import cv2
import bs4
import requests
import cfscrape
import string
import numpy
import os
import urllib3

from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)

class Utility:
    @staticmethod
    def Cv2Resize(image, width=None, height=None, inter=cv2.INTER_AREA):
        dim = None
        (h, w) = image.shape[:2]

        if width is None and height is None:
            return image
        if width is None:
            r = height / float(h)
            dim = (int(w * r), height)
        else:
            r = width / float(w)
            dim = (width, int(h * r))

        return cv2.resize(image, dim, interpolation=inter)

class LightshotCode:
    def __init__(self):
        self.base = list(string.ascii_lowercase) + list(string.digits)

    def parse(self, code):
        code = list(code)
        codeLength = len(code)
        self.size = codeLength
        self.items = list(map(lambda c: self.base.index(c), code))

    def increment(self):
        length = len(self.items)-1

        self.items[length] += 1
        baseLength = len(self.base) - 1

        for index in range(length, -1, -1):
            item = self.items[index]

            if item > baseLength:
                self.items[index] = 0
                
                if index == baseLength:
                    self.items = self.base[0] + self.items
                else:
                    self.items[index - 1] += 1
    
    def decrement(self):
        length = len(self.items) - 1

        self.items[length] -= 1
        baseLength = len(self.base) - 1

        for index in range(length, -1, -1):
            item = self.items[index]

            if item < 0:
                self.items[index] = baseLength 
                self.items[index - 1] -= 1

    def value(self):
        return sum(self.components)

    def string(self):
        return self.__str__()

    def __str__(self):
        return "".join(list(map(lambda i: self.base[i], self.items)))

class Program:
    @staticmethod
    def Main(arguments):
        start = arguments.start
        startcode = LightshotCode()
        startcode.parse(start)

        if not os.path.exists("images"):
            os.mkdir("images")
        
        with requests.Session() as session:
            session.headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36 OPR/67.0.3575.137"}
            # scraper = cfscrape.create_scraper(sess=session)
            scraper = session
            #scraper.proxies.update({
            #    "http": "http://192.168.0.77:8888",
            #    "https": "https://192.168.0.77:8888"
            #})
            scraper.verify=False
            protocol = "https"
            domain = "prnt.sc"
            prnt = protocol + "://" + domain + "/"

            while True:
                url = prnt + str(startcode)
                response = scraper.get(url)

                print(str(startcode), end="")

                if response.status_code == 200:
                    bs = bs4.BeautifulSoup(response.content, "lxml")
                    images = bs.select(".image__pic img")
                    operation = startcode.increment

                    if images:
                        if len(images) > 0:
                            image = images[0]
                            src = image["src"]

                            # missing image name
                            if not src.endswith("0_173a7b_211be8ff.png"):
                                response = session.get(src, stream=True, allow_redirects=False)

                                if response.status_code == 200:
                                    try:
                                        response.raw.decode_content = True
                                        _bytes = response.raw.read()

                                        nparr = numpy.frombuffer(_bytes, numpy.uint8)
                                        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                                        img = Utility.Cv2Resize(img, height=800)
                                        img = Utility.Cv2Resize(img, width=800)

                                        cv2.imshow(str(startcode), img)
                                        key = cv2.waitKey(0)

                                        # ANY OTHER KEY BESIDES ENTER/ESC MEANS TO GO TO THE NEXT IMAGE
                                        # ENTER = DOWNLOAD
                                        if key == 13 or key == 53:
                                            with open("images/"+str(startcode)+".png", "wb") as iio:
                                                print(" - DOWNLOADED")
                                                iio.write(_bytes)
                                                iio.flush()
                                                iio.close()
                                        # ESC = EXIT
                                        elif key == 27:
                                            print(" - EXIT")
                                            exit()
                                        # LEFT ARROW
                                        elif key == 97 or key == 52:
                                            operation = startcode.decrement
                                        elif key == 100 or key == 54:
                                            operation = startcode.increment

                                        cv2.destroyAllWindows()
                                    except Exception as ex:
                                        print(ex)
                                else:
                                    print(" - DELETED")
                            else:
                                print(" - DELETED")

                    print()
                    operation()

    
    @staticmethod
    def Arguments(parser):
        parser.add_argument(
            "-s",
            "--start",
            type=str,
            required=True
        )

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()

        Program.Arguments(parser)
        Program.Main(parser.parse_args())
    except KeyboardInterrupt:
        pass

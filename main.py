# coding: utf-8
__author__ = 'zhengyy'
from scrapy.cmdline import execute

import sys
import os


def main():
    print(os.path.abspath(__file__))
    print(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    execute(["scrapy", "crawl", "jobbole"])


if __name__ == "__main__":
    main()

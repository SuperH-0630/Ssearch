from abc import ABCMeta, abstractmethod
import requests
from bs4 import BeautifulSoup
import time


class Search(metaclass=ABCMeta):
    def __init__(self):
        self.url = ""
        self.args = ""
        self.bd_session = requests.Session()
        self.report = None
        self.bs4: BeautifulSoup = None
        self.word_list = []
        self.page_num = 0
        self.referer = ""
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'max-age=0',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'connection': 'close',
            'upgrade-insecure-requests': '1',
            'accept-encoding': 'gzip, deflate',
            "content-type": "application/x-www-form-urlencoded",
            "Upgrade-Insecure-Requests": "1",
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE',
        }

    @abstractmethod
    def get_report(self, args_list, start):
        pass

    @abstractmethod
    def bs_paser(self):
        pass

    @abstractmethod
    def find_word(self):
        pass

    @abstractmethod
    def __iter__(self):
        pass

    @abstractmethod
    def __next__(self):
        pass

    @abstractmethod
    def output_word(self):
        pass

    @abstractmethod
    def return_page(self):
        pass


class BingWeb(Search):
    def __init__(self):
        super().__init__()
        self.url = "https://cn.bing.com"
        self.headers["Origin"] = "https://cn.bing.com"
        self.headers['host'] = 'cn.bing.com'

    def get_report(self, args_list=None, start=True):
        if args_list:
            self.args = "?" + "q=" + args_list

        if start:
            self.page_num = 0

        if self.referer:
            self.headers["referer"] = "self.referer"
        self.referer = self.url + self.args
        self.report = self.bd_session.get(self.referer, headers=self.headers).text
        self.bs_paser()
        return self

    def bs_paser(self) -> None:
        assert self.report, "Don't get report"
        self.bs4 = BeautifulSoup(self.report, 'html.parser')

    def find_word(self) -> None:
        self.word_list = []

        word = self.bs4.find_all("li", class_="b_algo")
        for w in word:
            title = w.find("div", class_="b_title")
            try:  # 错误捕捉
                if title:  # 找到了title(官网模式)
                    self.word_list.append((title.h2.a.text, title.h2.a.get("href")))
                else:  # 普通词条模式
                    self.word_list.append((w.h2.a.text, w.h2.a.get("href")))
            except AttributeError:
                pass

    def __iter__(self):
        self.page_num = -1
        return self

    def __next__(self) -> bool:
        if self.page_num == -1:  # 默认的第一次get
            self.page_num += 1
            return True

        self.page_num += 1
        title = self.bs4.find("a", title=f"下一页")
        if title:
            self.args = title.get("href")
            self.report = self.get_report(None, False)
        else:
            raise StopIteration

        return True

    def output_word(self):
        return self.word_list

    def return_page(self):
        return self.page_num


class Seacher:  # 搜索者
    def __init__(self, word: str):
        self.web = {"bing": BingWeb()}
        self.word = word
        self.first = True

    def find(self):
        for web_name in self.web:
            web = self.web[web_name]
            web.get_report(self.word).__iter__()  # 做好迭代的准备
        return self

    def __iter__(self):
        self.first = True
        return self

    def __next__(self):
        if not self.first:
            time.sleep(1)
            # 使用了menu之后不需要is_next了
            # if not self.is_next():
            #     raise StopIteration
        else:
            self.first = False

        return_str = ""
        for web_name in self.web:
            web = self.web[web_name]
            try:
                web.__next__()
            except StopIteration:
                pass
            else:
                web.find_word()
                get: list = web.output_word()
                return_str += "\n" + "* " * 20 + f"\n{web.return_page()}: [{web_name}] for {self.word} >>>\n"
                for i in get:
                    return_str += f"{i[0]}\n        -> {i[1]}\n"
                return_str += "* " * 20 + "\n"
        return return_str

    def out_again(self):  # 再输出一次
        return_str = ""
        for web_name in self.web:
            web = self.web[web_name]
            get: list = web.output_word()
            return_str += "\n" + "* " * 20 + f"\n{web.return_page()}: [{web_name}] for {self.word} >>>\n"
            for i in get:
                return_str += f"{i[0]}\n{' ' * 8}-> {i[1]}\n"
            return_str += "* " * 20 + "\n"
        return return_str

    @staticmethod
    def is_next():
        return input("next? [Y/n]") != "n"


class Menu:
    def __init__(self):
        self.searcher_dict = {}
        print("Welcome To SSearch!")

    def menu(self) -> None:
        while True:
            try:
                if not self.__menu():
                    break
            except KeyboardInterrupt:
                print("Please Enter 'q' to quiz")
            except BaseException as e:
                print(f"There are some Error:\n{e}\n\n")

    def __menu(self):
        command = input("[SSearch] > ")  # 输入一条指令
        if(command == "q"):
            return False
        try:
            exec(f"self.func_{command}()")
        except AttributeError:
            print("Not Support Command. [help]")
        return True

    def func_make(self):
        word = input("输入关键词:")
        name = input(f"输入名字[默认={word}]:")
        if not name:
            name = word
        self.searcher_dict[name] = Seacher(word)  # 制造一个搜索器
        self.searcher_dict[name].find().__iter__()  # 迭代准备

    def func_again(self):
        name = input(f"输入名字:")
        seacher_iter = self.searcher_dict.get(name, None)
        if not seacher_iter:
            print("没有找到对应搜索器或搜索器已经搜索结束")
        else:
            print(seacher_iter.out_again())

    def func_next(self):
        name = input("输入名字:")
        seacher_iter = self.searcher_dict.get(name, None)
        if not seacher_iter:
            print("没有找到对应搜索器或搜索器已经搜索结束")
        else:
            try:
                print(seacher_iter.__next__())
            except StopIteration:
                print("搜索结束")
            except AttributeError as e:
                print(f"There are some Error:\n{e}\n\n")


menu = Menu()
menu.menu()

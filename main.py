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
        self.url_dict = {}
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

        # bing 特色搜索
        word = self.bs4.find_all("li", class_="b_ans")  # bing 词典(dict_oa), bing 视频(vsa)
        for w in word:
            dict_oa = w.find("div", class_="dict_oa")
            vsa = w.find("div", class_="vsa")  # bing 视频
            try:  # 错误捕捉
                if dict_oa:  # 找到了dict_oa，是词典模式
                    self.append_word_list("[bing词典]" + dict_oa.div.div.h2.a.text,
                                          self.url + dict_oa.div.div.h2.a.get("href"))
                elif vsa:  # 视频模式
                    self.append_word_list("[bing视频]" + vsa.h2.a.text,
                                          self.url + vsa.h2.a.get("href"))
                    pass
            except AttributeError:
                pass

        word = self.bs4.find_all("li", class_="b_ans b_mop b_imgans b_imgsmall")  # bing 图片
        for w in word:
            irphead = w.find("div", class_="irphead")
            try:  # 错误捕捉
                if irphead:  # 找到了dict_oa，是词典模式
                    self.append_word_list("[bing图片]" + irphead.h2.a.text,
                                          self.url + irphead.h2.a.get("href"))
            except AttributeError:
                pass

        word = self.bs4.find_all("li", class_="b_algo")  # b_algo是普通词条或者官网(通过b_title鉴别)
        for w in word:
            title = w.find("div", class_="b_title")
            try:  # 错误捕捉
                if title:  # 找到了title(官网模式)
                    self.append_word_list(title.h2.a.text, title.h2.a.get("href"))
                else:  # 普通词条模式
                    self.append_word_list(w.h2.a.text, w.h2.a.get("href"))
            except AttributeError:
                pass

    def append_word_list(self, title, url):  # 过滤重复并且压入url_list
        if not self.url_dict.get(url, None):
            self.url_dict[url] = title
            self.word_list.append((title, url))

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
                print("Please Enter 'quiz' or 'q' to quiz")
            except BaseException as e:
                print(f"There are some Error:\n{e}\n")

    def __menu(self):  # 注: self是有作用的(exec)
        command = input("[SSearch] > ")  # 输入一条指令
        if command == "q" or command == "quiz":
            print("SSearch: Bye Bye!")
            return False  # 结束
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
        self.func_next(name, True)

    def func_again(self, name=None):
        if not name:
            name = input(f"输入名字:")
        seacher_iter = self.searcher_dict.get(name, None)
        if not seacher_iter:
            print("没有找到对应搜索器或搜索器已经搜索结束")
        else:
            print(seacher_iter.out_again())

    def func_next(self, name=None, first=False):
        if not name:
            name = input(f"输入名字:")
        if not first:
            self.func_again(name)

        seacher_iter = self.searcher_dict.get(name, None)
        if not seacher_iter:
            print("没有找到对应搜索器或搜索器已经搜索结束")
        else:
            try:
                if first:  # make的时候需要输出
                    out = seacher_iter.__next__()
                    print(out)
                seacher_iter.__next__()  # 储备输出
            except StopIteration:
                self.func_again(name)  # 输出最后的结果
                del self.searcher_dict[name]  # 删除输出
                print(f"{name}: [搜索结束]")
            except AttributeError as e:
                print(f"There are some Error:\n{e}\n")


if __name__ == "__main__":
    menu = Menu()
    menu.menu()

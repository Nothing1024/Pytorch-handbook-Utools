import requests
from bs4 import BeautifulSoup

# 侧边栏获取地址
def get_category_list():
    url = "https://pytorch.org/docs/stable/torch.html"
    header = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.105 Safari/537.36'}
    default_str = "https://pytorch.org/docs/stable/"
    category_list = []
    category_list.append(default_str+"torch.html")
    try:
        r = requests.get(url, headers=header)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, 'html.parser')
        for i in soup.find_all("ul"):
            if i.has_attr("class") and i["class"][0] == "current":
                for j in i.find_all("li"):
                    if j.a.has_attr("href") and j.a["href"] != "#":
                        category_list.append(default_str+j.a["href"])
        category_list.pop()
        category_list = list(map(lambda x:x.replace("https://pytorch.org/docs/", ""), category_list))
        return category_list
    except Exception as e:
        print("爬取失败",e.__str__())

def extract_HTML(url):
    # 提取HTML：最精简版本，无CSS，Utools用
    header = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.105 Safari/537.36'}
    try:
        r = requests.get(url, headers=header)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, 'html.parser')
        # 遍历才能删除,如果归到一起好像会报错，所以这里暂时略过
        for i in soup.find_all(["nav","footer"]): # 主标签
            i.decompose()
        for i in soup.find_all(id=["header-holder", "pytorch-page-level-bar","pytorch-page-level-bar","pytorch-content-right","docs-tutorials-resources"]): # id标签
            i.decompose()
        for i in soup.find_all(class_=["table-of-contents-link-wrapper","cookie-banner-wrapper","mobile-main-menu"]): # class标签
            i.decompose()
        for i in soup.find_all("img"): # img标签 删除谷歌指数标签
            if i.has_attr('height') and type(eval(i['height'])) == int and int(i['height']) < 2:
                i.decompose()
        for i in soup.find_all("script"): # script标签
            i.decompose()
        for i in soup.find_all("link"): # link标签
            i.decompose()
        for i in soup("text"): # 遍历才能删除
            if isinstance(i,Comment):
                i.extract()
        url = url.replace("https://pytorch.org/docs/", "")
        f = open(url , "w+", encoding='utf-8')
        f.write(str(soup.prettify()))
    except Exception as e:
        print("爬取失败",e.__str__())

# 单页获取二级链接内容
def getJsonFormat(category):
    default_url = "https://pytorch.org/docs/"
    import re
    temp_list = [] # 标题
    temp_url_list = [] # 标题对应URL
    this_url = category
    father = "." + this_url.split("/")[-1].replace(".html" ,"")
    if father == ".torch":
        father = "torch"
    else:
        father = "torch" + father

    with open(this_url,encoding='utf-8',buffering=-1) as url_content:
        try:
            soup = BeautifulSoup(url_content.read(), 'html.parser')
            # 检测2列表格内容
            for i in soup.find_all("tr"):
                if len(i.find_all("td")) != 2: # 只检测2列表格
                    continue
                temp = i.find_all("td")[0]
                for temp in temp.find_all("a"):
                    temp["href"] = "stable/" + temp["href"]
                    if temp.has_attr("title"):
                        temp_list.append(
                            {"name":temp["title"],
                            "type": father,
                            "path":temp["href"],
                            "desc":re.sub(r"\s+", " ", i.find_all("td")[1].text.strip().replace("\n", "").replace(" .", "").replace(" ,", ""))}
                            )
                    else:
                        temp_list.append(
                            {"name":temp["href"].split(".html")[0],
                            "type": "torch" + father,
                            "path":temp["href"],
                            "desc":re.sub(r"\s+", " ", i.find_all("td")[1].text.strip().replace("\n", "").replace(" .", "").replace(" ,", ""))}
                            )
                    temp_url_list.append(default_url + temp["href"]) #单页获取，不进行dl处理
            # 检测非表格内容，即class td+id号内容
            for i in soup.find_all("dl"):
                if i.has_attr("class") and len(i["class"]) == 2 and i["class"][0] == "py" and i["class"][1] in ["function", "class"] :
                    temp_list.append(
                        {"name":i.dt["id"],
                        "type": "torch" + father,
                        "path":this_url+"#"+i.dt["id"],
                        "desc":re.sub(r"\s+", " ", i.dd.text.strip().replace("\n", "").replace(" .", "").replace(" ,", ""))
                          .split(".")[0] + "."} # 只截取第一句话
                        )
            return {
                "temp_list":temp_list,
                "temp_url_list":temp_url_list
            }
        except Exception as e:
            print("爬取失败",e.__str__())

import json
default_url = "https://pytorch.org/docs/"
json_dict = []
temp_list = []
temp_url_list = []
# TODO 先获取侧边栏内容
category_list = get_category_list()
# TODO 获取单主页地址  + 添加元素
for i in category_list[:-2]: # 一级目录链接开始循环 获取网页 + 加载信息
    extract_HTML(default_url + i)
    json_dict.append({
        "name": i.replace("stable/","").replace(".html",""),
        "type": "",
        "path": i,
        "desc": ""
    })
    # TODO 获取二级地址对应元素
    tmp_dict = getJsonFormat(i)
    # TODO 拼接
    if tmp_dict['temp_list']:
        temp_list.extend(tmp_dict['temp_list'])
    if tmp_dict['temp_url_list']:
        temp_url_list.extend(tmp_dict['temp_url_list'])
# TODO 二级地址全部开始爬
for i in temp_url_list:
    if "#" in i:
        extract_HTML(i.split("#")[0])

json_str = json.dumps(temp_list)
with open('pytorch.json', 'w+') as json_file:
    json_file.write(json_str)

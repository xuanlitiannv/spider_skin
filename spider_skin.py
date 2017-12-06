import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from pymongo import MongoClient

#建立MonogoDB数据库连接
client=MongoClient('localhost',27017)
#连接所需数据库，test为数据库名
db=client.test
#连接所用集合 info_content帖子元数据表，content_comment帖子评论表
collection1=db.info_content
collection2=db.content_comment

domain_url = 'http://bbs.lady8844.com'
url = 'http://bbs.lady8844.com/forum-76-1.html' #美容护肤
#url='http://bbs.lady8844.com/forum-93-1.html' #美发护发
#url='http://bbs.lady8844.com/forum-30-1.html' #潮流穿搭
#url='http://bbs.lady8844.com/forum-48-1.html' #免费试用
# 创建一个driver用于打开网页
driver = webdriver.Chrome('C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe')
driver.get(url) # 打开网页

page = 0;
while page<2010:
    print(page)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    titles=soup.find_all('tbody')
    for title in titles:
          threads = title.find_all('a',{"class":"s xst"})
          sender_names = title.select('cite a')
          content_dates = title.select('em span')
          reply_nums=title.select('td.num a')
          for thread in threads:
              t = thread['href']
              #print(t)
		      #帖子的入口地址
              id_inaddress = domain_url+"/" + t
              #print(id_inaddress)
		      #帖子的id
              content_id = "content_"+t[7:-9]
              #print(content_id)
		      #帖子的标题
              content_title = thread.string
              #print(content_title)
              #发帖人的名字
              sender_name = str(sender_names)[34:-5]
              #print(sender_name)
              #发帖人的入口地址
              size = int(-(len(sender_name)+7))
              sender_address = domain_url+"/"+str(sender_names)[10:size]
              #print(sender_address)
              #发帖的日期
              content_date =str(content_dates)[7:-8]
              #print(content_date)
              #发帖的回复数
              reply_num=reply_nums[0].string
              #print(reply_num)
              content_id_exist=collection1.find_one({"content_id":content_id})
              info_content=collection1.find({})
              #表空或者帖子的id不存在
              if (not info_content) or (content_id_exist==None):
				  #查找内容
                  print("表空或者帖子的id不存在")
                  res_child = requests.get(id_inaddress)
                  html = res_child.content.decode('utf-8')
                  soup_child = BeautifulSoup(res_child.text, "lxml")
                  content_comments = soup_child.find_all("div", {"class": "pg"})
                  # 如果存在，解析全部range,如果不存在就解析一页
                  if content_comments:
                      # 找到每一个帖子当中共需解析多少页
                      content_comments = content_comments[0].find_all("span")
                      # print(content_comments)
                      markup = str(content_comments)
                      child_pages = BeautifulSoup(markup, "lxml")
                      child_page = child_pages.get_text()[3:-3]
                      #print(child_page)
                      # 解析每个帖子每一页的发布的内容和回复
                      for j in range(int(child_page) + 1):
                          s = ""
                          if j == 0:
                              res_child_page = requests.get(domain_url)
                          else:
                              # 截取页面共有的路径部分
                              child_url = id_inaddress[0:-8]
                              child_all_url = child_url + str(j) + "-" + str(page+1) + ".html"
                              print(child_all_url)
                              res_child_page = requests.get(child_all_url)
                              html = res_child_page.content.decode('utf-8')
                              soup_child_page = BeautifulSoup(res_child_page.text, "lxml")
                              # 查找一个帖子的全部内容和回复
                              comment_comment_all = soup_child_page.find_all("td", {"class": "t_f"})
                              replyer_names = soup_child_page.find_all('a', {"class": "xw1"})
                              types = soup_child_page.select('div.z a')
                              #帖子的类型
                              type=types[3].string
                              #print(type)
                              length = len(comment_comment_all)
                              com = []
                              for i in range(length):
                                  j = j + i
                                  if j == 1:
                                      #内容
                                      s = str(comment_comment_all[i].get_text().split())
                                      #print(s)
                                      collection1.insert({"content_id": content_id, "id_inaddress": id_inaddress,
                                                         "content_title": content_title, "sender_name": sender_name,
                                                         "sender_address": sender_address, "content_date": content_date,
                                                         "reply_num": reply_num ,"content":s,"type":type})
                                  else:
                                      # 回帖人的入口地址
                                      replyer_address = domain_url + "/" + replyer_names[i]['href']
                                      #print(replyer_address)
                                      # 回帖人的名字
                                      replyer_name = replyer_names[i].string
                                      #print(replyer_name)
                                      # 帖子评论的id
                                      comment_id = comment_comment_all[i]['id']
                                      # print(comment_id)
                                      #评论
                                      s = str(comment_comment_all[i].get_text().split())
                                      #print(s)
                                      collection2.insert(
                                          {"content_id": content_id, "comment": s, "replyer_address": replyer_address,
                                           "replyer_name": replyer_name, "comment_id": comment_id})
                  else:
                      # 只有一页的帖子的发布和回复
                      comment_comment_all_onepage = soup_child.find_all("td", {"class": "t_f"})
                      replyer_names = soup_child.find_all('a', {"class": "xw1"})
                      types = soup_child_page.select('div.z a')
                      # 帖子的类型
                      type = types[3].string
                      #print(type)
                      length1 = len(comment_comment_all_onepage)
                      com_onepage = []
                      s = ""
                      for i in range(length1):
                          if i == 0:
                              #内容
                              s = str(comment_comment_all_onepage[i].get_text().split())
                              # print(s)
                              collection1.insert({"content_id": content_id, "id_inaddress": id_inaddress,
                                                 "content_title": content_title, "sender_name": sender_name,
                                                 "sender_address": sender_address, "content_date": content_date,
                                                 "reply_num": reply_num, "content":s,"type":type})
                          else:
                              #回帖人的入口地址
                              replyer_address = domain_url + "/" + replyer_names[i]['href']
                              #print(replyer_address)
                              #回帖人的名字
                              replyer_name = replyer_names[i].string
                              #print(replyer_name)
                              #帖子评论的id
                              comment_id = comment_comment_all_onepage[i]['id']
                              # print(comment_id)
                              #评论
                              s = str(comment_comment_all_onepage[i].get_text().split())
                              # print(s)
                              collection2.insert({"content_id":content_id,"comment":s ,"replyer_address":replyer_address,"replyer_name":replyer_name,"comment_id":comment_id})
              else:
                    print("存在content_id")
                    #表info_content存在content_id,判断回复数是否相同，若不同则删除content_comment中与之关联的评论，重新插入新的评论
                    for rereply_names in collection1.find({"content_id": content_id}, {"reply_num": 1, "_id": 0}):
                         rereply_num=str(rereply_names)[15:-2]
                         if rereply_num != reply_num:
                             collection1.update({'content_id':content_id},{'$set':{'reply_num':reply_num}})
                             print(reply_num)
                             collection2.remove({'content_id': content_id})
                             #重新查找回复
                             reres_child = requests.get(id_inaddress)
                             html = reres_child.content.decode('utf-8')
                             resoup_child = BeautifulSoup(reres_child.text, "lxml")
                             recontent_comments = resoup_child.find_all("div", {"class": "pg"})
                             # 如果存在，解析全部range,如果不存在就解析一页
                             if recontent_comments:
                                 # 找到每一个帖子当中共需解析多少页
                                 recontent_comments = recontent_comments[0].find_all("span")
                                 # print(recontent_comments)
                                 markup = str(recontent_comments)
                                 rechild_pages = BeautifulSoup(markup, "lxml")
                                 rechild_page = rechild_pages.get_text()[3:-3]
                                 #print(rechild_page)
                                 # 解析每个帖子每一页的发布的回复
                                 for j in range(int(rechild_page) + 1):
                                     s = ""
                                     if j == 0:
                                         reres_child_page = requests.get(domain_url)
                                     else:
                                         # 截取页面共有的路径部分
                                         rechild_url = id_inaddress[0:-8]
                                         rechild_all_url = rechild_url + str(j) + "-" + str(page + 1) + ".html"
                                         print(rechild_all_url)
                                         reres_child_page = requests.get(rechild_all_url)
                                         html = reres_child_page.content.decode('utf-8')
                                         resoup_child_page = BeautifulSoup(reres_child_page.text, "lxml")
                                         # 查找一个帖子的全部内容和回复
                                         recomment_comment_all = resoup_child_page.find_all("td", {"class": "t_f"})
                                         rereplyer_names = resoup_child_page.find_all('a', {"class": "xw1"})
                                         relength = len(recomment_comment_all)
                                         com = []
                                         m=0
                                         for i in range(relength):
                                             j = j + i
                                             if j != 1:
                                                 # 回帖人的入口地址
                                                 replyer_address = domain_url + "/" + rereplyer_names[i]['href']
                                                 # print(replyer_address)
                                                 # 回帖人的名字
                                                 replyer_name = rereplyer_names[i].string
                                                 # print(replyer_name)
                                                 # 帖子评论的id
                                                 comment_id = recomment_comment_all[i]['id']
                                                 # print(comment_id)
                                                 # 评论
                                                 s = str(recomment_comment_all[i].get_text().split())
                                                 # print(s)
                                                 collection2.insert(
                                                     {"content_id": content_id, "comment": s,
                                                      "replyer_address": replyer_address,
                                                      "replyer_name": replyer_name, "comment_id": comment_id})
                             else:
                                 recomment_comment_all_onepage = resoup_child.find_all("td", {"class": "t_f"})
                                 rereplyer_names = resoup_child.find_all('a', {"class": "xw1"})
                                 relength1 = len(recomment_comment_all_onepage)
                                 recom_onepage = []
                                 s = ""
                                 for i in range(relength1):
                                     if i != 0:
                                         # 回帖人的入口地址
                                         replyer_address = domain_url + "/" + rereplyer_names[i]['href']
                                         # print(replyer_address)
                                         # 回帖人的名字
                                         replyer_name = rereplyer_names[i].string
                                         # print(replyer_name)
                                         # 帖子评论的id
                                         comment_id = recomment_comment_all_onepage[i]['id']
                                         # print(comment_id)
                                         # 评论
                                         s = str(recomment_comment_all_onepage[i].get_text().split())
                                         # print(s)
                                         collection2.insert({"content_id": content_id, "comment": s,
                                                             "replyer_address": replyer_address,
                                                             "replyer_name": replyer_name, "comment_id": comment_id})

    driver.find_element_by_xpath("//a[contains(text(),'下一页')]").click()
    # selenium的xpath用法，找到包含“下一页”的a标签去点击
    page = page + 1
    time.sleep(2)  # 睡2秒让网页加载完再去读它的html代码
driver.quit()



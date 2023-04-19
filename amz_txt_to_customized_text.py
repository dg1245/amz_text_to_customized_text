import os
import csv
import requests
import zipfile
import json

# Author: dg1245@qq.com
# 出现错误自己解决，不提供售后，副作用未知，amz账号搞挂了自己负责
# 思路：amz后台下载txt--找到里面每个订单对应的url--下载zip压缩包并解压缩--解析json即可
# 没有下载失败后重试的代码，自己添加
# 这是好早之前写的代码了，只能获取下拉菜单和用户输入的文字
# 突然发现json新增了version3.0，感觉解析起来会更简单，以后有空再更新

# 每一个url下载后，压缩包都叫temp.zip
# 下载前先把已经存在的temp.zip删掉
def download_zip(url):
    try:
        filename = "temp.zip"
        if os.path.exists(filename):
            os.remove(filename)
            # print(filename + " removed successfully")

        r = requests.get(url, stream=True)

        with open(filename, 'wb') as code:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    code.write(chunk)
        # print('download ' + filename + ' successfully')
    except:
        pass


# 下载一个压缩包并解压缩，解析json，删掉压缩包，再下载下一个压缩包
def unzip_and_get_json():
    filename = "temp.zip"
    z = zipfile.ZipFile(filename, 'r')
    for f in z.namelist():
        if f[-4:] == 'json':
            json_file_name = f
            content = z.read(json_file_name)
            # 抄的代码，忘了是干啥的
            with open(json_file_name, 'wb') as code:
                code.write(content)
            with open(json_file_name, 'r', encoding='utf8') as js:
                data = json.load(js)

                orderId = data['orderId']
                asin = data['asin']
                title = data['title']
                # 打开json，自己慢慢琢磨吧，提示，可以画一个树状图
                if data['customizationData']['type'] == "PageContainerCustomization":
                    customizationData = data['customizationData']['children'][0]['children'][0]['children']
                else:
                    customizationData = data['customizationData']['children'][0]['children']

                # 客户一个订单买了几款定制产品，别跟quantity搞混了
                # 大部分客户一个订单，买1款产品，数量是1，举例，客户买了1个红色的
                # 少部分客户一个订单，买1款产品，数量是2，举例，客户买了2个红色的，定制内容一模一样
                # 少部分客户一个订单，买多款产品，每个产品数量1个或多个，举例，客户买了2个红色的（定制信息一模一样），1个蓝色
                # 客户的一个订单，买了len(customizationData)款产品，每个产品的是quantity个
                # 但是，也不排除客户买了2款产品，规格和定制信息都是一模一样的，比如客户买了1个红色，又买了1个红色，定制信息一模一样
                # order detail
                # first product - 2 pcs
                # second product - 1 pcs
                # len(customizationData) is 2, quantity is 2 and 1, totol quantity is 3
                # 应该是这样的，好早之前写的代码了，记忆模糊了
                for i in range(len(customizationData)-1):
                    customized_option_data = customizationData[i]
                    print(customized_option_data['name'] + ": " + customized_option_data['optionSelection']['label'])

                customized_txt_data = customizationData[len(customizationData)-1]['children']

                for j in range(len(customized_txt_data)):
                    for k,v in customized_txt_data[j].items():
                        # 下拉菜单的内容
                        if k == 'type' and v == 'FontCustomization':
                            head = customized_txt_data[j]['label']
                            tail = customized_txt_data[j]['fontSelection']['family']
                            print(head + ": " + tail)

                        elif k == 'type' and v == 'ColorCustomization':
                            head = customized_txt_data[j]['label']
                            tail = customized_txt_data[j]['colorSelection']['name']
                            print(head + ": " + tail)

                        elif k == 'type' and v == 'ContainerCustomization':

                            number = len(customized_txt_data[j]['children'])
                            # 客户输入的文字内容，json也会改版，记得微调
                            for i in range(number):
                                try:
                                    head = customized_txt_data[j]['children'][i]['children'][0]['children'][0]['label']
                                    tail = customized_txt_data[j]['children'][i]['children'][0]['children'][0]['inputValue']
                                except:
                                    head = customized_txt_data[j]['children'][i]['children'][0]['label']
                                    tail = customized_txt_data[j]['children'][i]['children'][0]['inputValue']
                                print(head + ": " + tail)
                            # 没有图片定制的需求，也就没写代码（没有json内容也不知道怎么写）
                            # 猜测应该会给一个图片链接，下载即可

    # 把json文件删掉
    if os.path.exists(json_file_name):
        os.remove(json_file_name)
        # print(json_file_name + " removed successfully")


# 去amz后台下载txt文档，可直接用excel打开查看
# 下载路径：amz后台--Orders--Order Reports--Type of report: Order Date--Event Date: Last day--Request--Download
# 只包含了获取定制信息里的下拉菜单，客户输入的内容；定制图片等其余功能我用不到，也获取不到txt，这一部分就没有了


# start here
files = os.listdir()
for file in files:
    if os.path.splitext(file)[-1] == ".txt":
        with open(file, 'r') as f:
            reader = csv.reader(f, delimiter="\t")

            for index, row in enumerate(reader):
                # 测试为了效率，可以改成 if index == 1 只测试某订单号的数据是否有效显示
                # if index == 1:
                # 第0行是表头，所以index从1开始
                if index in range(1, 999):
                    try:
                        # amz经常改版，记得更新对应的位置
                        orderID = row[0]
                        # url是zip压缩包的下载地址，里面的json文件包含了定制信息
                        url = row[38]
                        title = row[10]
                        quantity = row[13]
                        # 现在只能看到城市，州，邮编，国家，看不到街道地址
                        address = ','.join(row[28:32])

                        if url:
                            print("#########################")
                            print('orderID:', orderID)
                            print('url:', url)
                            print('title:', title)
                            print('quantity:', quantity)
                            print('address:', address)

                            download_zip(url)
                            try:
                                unzip_and_get_json()
                            except:
                                pass
                    except:
                        pass





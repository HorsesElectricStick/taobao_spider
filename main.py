"""
主程序功能
1、定时任务设置
2、接收爬虫返回的订单详情，解析并存入数据库
"""
from MySql import MysqlBase
from spider import Spider
from apscheduler.schedulers.blocking import BlockingScheduler

def save_info(result: list):
    mysql = MysqlBase()
    # 传入的result为list，result[0]为'info'，表示订单详情，result[0]为'error'则为错误信息，存入日志
    if result[0] == 'info':
        # 订单详情插入information表
        for i in range(1,len(result)):
            # 判断订单详情是否已经存在
            exist = mysql.getOne("select * from information where `order_number` = %s",(result[i]['order_number']))
            if exist:
                mysql.update("update information set express_info=%s , update_time=now() where order_number=%s",(result[i]['express_info'],result[i]['order_number']))
                mysql.end()
            else:
                mysql.insert("insert into information(id,title,order_number,order_date,store,price,amount,payment,status,"
                             "express_info,update_time) values(null,%s,%s,%s,%s,%s,%s,%s,%s,%s,now())",
                             (result[i]['title'],result[i]['order_number'],result[i]['order_date'],result[i]['store'],
                              result[i]['price'],result[i]['amount'],result[i]['payment'],result[i]['status'],result[i]['express_info']))
                mysql.end()
    return


def run():
    runner = Spider()
    result = runner.get_info()
    save_info(result)

# 定时任务
def dojob():
    scheduler = BlockingScheduler()
    scheduler.add_job(run,'interval',seconds=1200,id='taobao_job1')
    scheduler.start()


if __name__ == '__main__':
    dojob()

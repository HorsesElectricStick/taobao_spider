import random, time
from MySql import MysqlBase
from pyquery import PyQuery as pq
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class Spider(object):
    mysql = MysqlBase()
    chrome_options = Options()
    # 设置UA
    chrome_options.add_argument(
        'user-agent="Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60"')
    # 设置无头浏览器
    # chrome_options.add_argument('--headless')
    # 设置滚动条
    chrome_options.add_argument('--hide-scrollbars')
    # 设置最高权限
    chrome_options.add_argument('--no-sandbox')
    # 设置开发者模式
    # chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_argument('--disable-gpu')
    browser = webdriver.Chrome(chrome_options=chrome_options)
    browser.maximize_window()
    # 等待条件，超出时间仍未加载完成抛出异常
    wait = WebDriverWait(browser, 10)

    # 模拟登陆
    def _login(self) -> str:
        login_url = 'https://login.taobao.com'
        user_name = '用户名'
        password = '密码'

        try:
            self.browser.get(login_url)
            # 用户名输入框
            input_user_name = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#fm-login-id'))
            )
            # 密码输入框
            input_password = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#fm-login-password'))
            )
            # 登录按钮
            submit = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '#login-form > div.fm-btn > button'))
            )
            input_user_name.send_keys(user_name)
            time.sleep(1)
            input_password.send_keys(password)
            time.sleep(1)
            submit.click()
            # 需要验证码处理
            if self.wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#login-error > div'), '请拖动滑块完成验证')):
                self._captcha()
            if self.wait.until(EC.text_to_be_present_in_element(
                    (By.CSS_SELECTOR, '#J_SiteNavLogin > div.site-nav-menu-hd > div.site-nav-user > a'), '可可可可熊熊熊')):
                return '登陆成功'
            else:
                return '登陆失败'
        except TimeoutException as error:
            return error.__str__()

    # 获取订单详情
    def _parse_items(self) -> dict:
        # #tp-bought-root > div > div > table > tbody:nth-child(3) > tr:nth-child(1) > td:nth-child(1) > div > div:nth-child(2) > p:nth-child(1) > a:nth-child(1) > span:nth-child(2)
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.index-mod__order-container___1ur4-')))
        html = self.browser.page_source
        count = 0
        doc = pq(html)
        items = doc('.index-mod__order-container___1ur4-').items()
        for item in items:
            result = {
                'title': item.find('tr:nth-child(1) p:nth-child(1) > a:nth-child(1) > span:nth-child(2)').text().strip(),
                'order_number': item.find('td > span > span:nth-child(3)').text().strip(),
                'order_date': item.find('tbody >tr >td > label > span:nth-child(2)').text().strip(),
                'store': item.find('td > span > a').text().strip(),
                'price': item.find('tbody:nth-child(3) > tr:nth-child(1) > td:nth-child(2) > div > p > span:nth-child(2)').text().strip(),
                'amount': item.find('tbody:nth-child(3) > tr:nth-child(1) > td:nth-child(3) > div > p').text().strip(),
                'payment': item.find('tbody:nth-child(3) > tr:nth-child(1) > td:nth-child(5) > div > div.price-mod__price___cYafX > p > strong > span:nth-child(2)').text().strip(),
                'status': item.find('tbody:nth-child(3) > tr:nth-child(1) > td:nth-child(6) > div > p > span').text().strip(),
            }
            print(result)
            # 对订单状态不是'交易成功'的订单，获取对应的物流信息
            if result['status'] == '卖家已发货':
                result['express_info'] = self._get_express_info(count)
            else:
                result['express_info'] = None
            count += 1
            yield result

    # 获取物流信息
    def _get_express_info(self,i) -> str:
        content = ''
        i = i+4
        button = self.browser.find_element_by_xpath('//*[@id="tp-bought-root"]/div[{}]//*[@id="viewLogistic"]'.format(i))
        time.sleep(2)
        button.click()
        windows = self.browser.window_handles
        self.browser.switch_to.window(windows[1])
        if 'detailnew' in self.browser.current_url:
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.feed-list > li')))
            doc = pq(self.browser.page_source)
            items = doc('.feed-list > li').items()
            for item in items:
                content += item.text()
                content += '\n'
            self.browser.close()
            windows = self.browser.window_handles
            self.browser.switch_to.window(windows[0])
            return content

        else:
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.status-box > ul:nth-child(1) > li')))
            doc = pq(self.browser.page_source)
            items = doc('.status-box > ul:nth-child(1) > li').items()
            for item in items:
                content += item.text()
                content += '\n'
            self.browser.close()
            windows = self.browser.window_handles
            self.browser.switch_to.window(windows[0])
            return content
        


    # 翻页操作
    def _next_page(self, page):
        input_box = self.wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, '#tp-bought-root > div.row-mod__row___3dZa8.js-actions-row-bottom > '
                             'div:nth-child(2) > ul > div > div > input[type=text]')))

        search_button = self.wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, '#tp-bought-root > div.row-mod__row___3dZa8.js-actions-row-bottom > '
                             'div:nth-child(2) > ul > div > div > span.pagination-options-go')))

        input_box.clear()
        input_box.send_keys(page)
        search_button.click()
        time.sleep(random.randint(3, 6))

    # 处理滑块验证码
    def _captcha(self):
        block = self.browser.find_element_by_css_selector('#nc_1_n1z')
        ActionChains(self.browser).click_and_hold(block).perform()
        x = random.randint(100, 400)
        ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
        x = 600 - x
        time.sleep(0.5)
        ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
        ActionChains(self.browser).release(on_element=block).perform()
        if self.wait.until(EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, '#nc_1__scale_text > span > b'), '验证通过')
        ):
            submit = self.browser.find_element_by_css_selector('#login-form > div.fm-btn > button')
            time.sleep(0.5)
            submit.click()
        else:
            refresh = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#nocaptcha-password > div > span > a')))
            refresh.click()
            time.sleep(2)
            self._captcha()

    def get_info(self) -> list:
        self.mysql.insert("insert into spider_info(id,spider,status,start_time) values(null,'spider.py',1,now())")
        self.mysql.end()
        id = self.mysql.getLastId()
        result = []
        login_info = self._login()
        # 返回错误信息
        if login_info != '登陆成功':
            result.append('error')
            result.append(login_info)
            self.mysql.update("update spider_info set status=0 , log=%s , end_time=now() ,execute_result=0 , count=0 where id=%s",(login_info,id))
            return result
        else:
            result.append('info')

        # 切换到已买到的宝贝
        bought_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#bought')))
        time.sleep(2)
        bought_button.click()

        # 总页数
        total_page = int(self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#tp-bought-root > div.row-mod__row___3dZa8.js-actions-row-bottom > div:nth-child(2) > ul > li:nth-last-child(3)'))).text)
        for i in self._parse_items():
            result.append(i)

        if total_page > 1:
            for i in range(2, total_page+1):
                self._next_page(i)
                for i in self._parse_items():
                    result.append(i)

        count = (len(result) - 1)
        self.mysql.update("update spider_info set status=0 , end_time=now() , log=%s , execute_result=1 , count=%s where id=%s",
                          (login_info,count, id))
        self.mysql.end()
        self.mysql.dispose()
        self.browser.quit()
        return result


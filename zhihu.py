# -*- coding: utf-8 -*-
__author__ = 'tengchuan.wang'
import os
import time
import requests
import re
import pickle
import json
import time

EXPIRE_TIME = 24 * 3600


class ZhihuCralwer(object):
    """docstring for ZhihuCralwer"""

    def __init__(self, config):
        super(ZhihuCralwer, self).__init__()
        self.base_url = config['url']
        self.email = config['email']
        self.password = config['password']
        self.header_base = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2',
            'Connection': 'keep-alive',
            'Host': 'www.zhihu.com',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.130 Safari/537.36',
            'Referer': 'http://www.zhihu.com/'
        }
        self.cookies = {}
        self._xsrf = ''

    def init_login(self):
        path = 'login/email'
        login_url = self.base_url + path
        login_data = {
            'email': self.email,
            'password': self.password,
            'remeberme': 'true',
            'captcha': ''
        }
        global s
        s = requests.session()
        timestamp = int(time.time()) * 1000
        captcha_url = self.base_url + 'captcha.gif?r=' + str(timestamp) + '&type=login'
        with open('captcha.gif', 'wb') as f:
            captcha_res = s.get(captcha_url)
            f.write(captcha_res.content)
        login_captcha = raw_input('请输入验证码\n').strip()
        login_data['captcha'] = login_captcha
        print '验证码是', login_captcha
        login_res = s.post(login_url, headers=self.header_base, data=login_data)
        print login_res.status_code
        if login_res.status_code == 200:
            homepage_res = s.get(self.base_url, headers = self.header_base)
            parse_xsrf = re.search(r'<input type="hidden" name="_xsrf" value="(\w*)"/>', homepage_res.text)
            xsrf = parse_xsrf.group(1)
            with open('xsrf', 'w') as f:
                f.write(str(xsrf))
        else:
            print '登录失败，程序即将退出'
            sys.exit(0)
        if os.path.exists('cookie_file') and os.stat('cookie_file').st_size > 0 and time.time() - os.stat('cookie_file').st_mtime < EXPIRE_TIME:
            with open('cookie_file', 'rb') as f:
                self.cookies = pickle.load(f)
        else:
            with open('cookie_file', 'w') as f:
                pickle.dump(
                    requests.utils.dict_from_cookiejar(res.cookies), f)
            self.cookies = res.cookies
        self.header_base['cookies'] = self.cookies

    def get_cookie(self):
        cookie_exists = os.path.exists('cookie_file') and os.stat('cookie_file').st_size > 0 and os.path.exists('xsrf')
        retry = 0
        while(!cookie_exists and retry < 3):
            self.init_login()
            retry += 1
        if not cookie_exists:
            print '登录失败，退出'
            sys.exit(0)
        else:
            with open('cookie_file', 'rb') as f:
                self.cookies = pickle.load(f)
            with open('xsrf', 'r') as f:
                self._xsrf = f.read()


    def save_xsrf(xsrf, account = None):
        #在本地先将xsrf存入文件，日后按照account帐号存入redis
        #file_name = account + '.xsrf'
        file_name = 'xsrf'
        with open(file_name, 'w') as f:
            f.write(str(xsrf))

    def parse_info(self, content=None):
        user_info = {
            'location': '',
            'education': '',
            'major': '',
            'agree': 0,
            'thanks': 0,
            'followees': 0,
            'followers': 0,
        }
        parse_location = re.search(
            r'<span class="location item" title="(.*?)"><a href=', content)
        parse_education = re.search(
            r'<span class="education item" title="(.*?)"><a href=', content)
        parse_education_major = re.search(
            r'<span class="education-extra item" title="(.*?)"><a href=', content)
        parse_agree = re.search(
            r'<span class="zm-profile-header-user-agree"><span class="zm-profile-header-icon"></span><strong>\d*</strong>赞同</span>', content)
        parse_thanks = re.search(
            r'<span class="zm-profile-header-user-thanks"><span class="zm-profile-header-icon"></span><strong>\d*</strong>感谢</span>')
        parse_followees = re.search(
            r'<span class="zg-gray-normal">关注了</span><br /><strong>\d*</strong><label> 人</label>')
        parse_followers = res.search(
            r'<span class="zg-gray-normal">关注者</span><br /><strong>\d*</strong><label> 人</label>')
        if parse_location:
            user_info['location'] = parse_location.group(1)
        if parse_education:
            user_info['education'] = parse_education.group(1)
        if parse_education_major:
            user_info['major'] = parse_education_major.group(1)
        if parse_agree:
            user_info['agree'] = parse_agree.group(1)
        if parse_thanks:
            user_info['thanks'] = parse_thanks.group(1)
        if parse_followees:
            user_info['followees'] = parse_followees.group(1)
        if parse_followers:
            user_info['followers'] = parse_followers.group(1)
        return user_info

    def get_user_info(self, user_id):
        url = self.base_url + 'people/' + user_id
        res = s.get(url, headers=self.header_base,
                    cookies=self.cookies)
        user_info = self.parse_info(res.text)
        SQL_INSERT_USER_INFO = '''insert into oceanus.zhihu_user(`user_id`, `location`, `education`, `major`, `agree`, `thanks`, `followees`, `followers`)
                                    values(%s, %s, %s, %s, %s)'''

    def get_followees_list(self, user_id):
        url = self.base_url + 'people/' + user_id + '/followees/'
        res = s.get(url, headers=self.header_base,
                    cookies=self.cookies)
        #followee_list = #这里需要用selenium模拟得到ajax数据

    def ajax_call(self):
        base_url = 'https://www.zhihu.com/node/ProfileFolloweesListV2'
        for index in range(20, 100, 20):
            params = {
                "offset":str(index),
                "order_by":"created",
                "hash_id":"d0f1eeab75474628202a41b497e006dd"
            }
            post_data = {'method': 'next',
                         'params': json.dumps(params),
                         '_xsrf': self._xsrf
            }
            print post_data
            res = s.post(base_url, headers = self.header_base, data = post_data)
            print res.text


if __name__ == '__main__':
    config = {}
    cwd = os.getcwd()
    config_file = cwd + '/zhihu.config'
    execfile(config_file, config)
    crawler = ZhihuCralwer(config)
    crawler.get_cookie()
    crawler.ajax_call()

import tornado.web
import tornado.httpclient
import asyncio
import yaml
import os

curPath = os.path.dirname(os.path.realpath(__file__))

class SDWANLogin(object):
    def __init__(self, vManage_ip, user_name, user_passwd) -> None:
        self.vManage_ip = vManage_ip
        self.user_name = user_name
        self.user_passwd = user_passwd
        self.token = None
        self.cookie = None
        self.status = 0
        # status failed--False  success--True
        # self.status = self.login(vManage_ip, user_name, user_passwd)


    async def login(self):
        """Login to vManage."""

        sdwan_url = "https://{}".format(self.vManage_ip)
        auth_action = "/j_security_check"
        # Url for posting login data
        auth_url = sdwan_url+auth_action

        # Request body for login post
        req_body = "j_username={}&j_password={}".format(self.user_name,self.user_passwd)
        # Request headers for login post
        req_headers={"Content-Type":"application/x-www-form-urlencoded"}
        
        # AsyncHTTPClient to make the post request
        client = tornado.httpclient.AsyncHTTPClient()
        auth_request = tornado.httpclient.HTTPRequest(auth_url, method="POST", headers=req_headers, body=req_body, validate_cert=False)
        auth_response = await client.fetch(auth_request)

        # print(auth_response.headers.get_list("Set-Cookie"))
        # Store the cookie
        self.cookie = auth_response.headers.get_list("Set-Cookie")[0]

        if auth_response.code == 200:
            if "Invalid" in str(auth_response.body):
                print("Invalid User or Password")
                self.status = 0
                # return False
            else:
                print("Login success")
                self.status = 1
                token_action = "/dataservice/client/token"
                # Url for getting token
                token_url = sdwan_url + token_action

                token_headers = {"Cookie": self.cookie}
                token_request = tornado.httpclient.HTTPRequest(token_url, method="GET", headers=token_headers, validate_cert=False)
                token_response = await client.fetch(token_request)
                if token_response.code == 200:
                    self.token = token_response.body.decode("utf-8")
                # return True
                self.update_cookie_token()

    def update_cookie_token(self):
        try:
            with open('config.yaml', 'r') as f1:
                config = yaml.safe_load(f1)
                f1.close()
            with open('config.yaml', 'w') as f2:
                config['cookie'] = self.cookie
                config['token'] = self.token
                print(config)
                yaml.dump(config,f2)
                f2.close()
        except Exception as e:
            print(e)

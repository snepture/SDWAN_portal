import tornado.web
import tornado.httpclient
import yaml
import json
import asyncio
from module.Login_control import LoginControl

class UserBaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("username")

class CloudAccountApi(UserBaseHandler):
    async def get(self):
        # Check user's validation
        if not self.current_user:
            print("Invalid login, please login again.")
            self.finish("Invalid login, please login again.")

        config = yaml.safe_load(open('config.yaml', 'r'))

        vpc_headers = {"Content-Type":"application/json", 
                       "cookie": config['cookie'],
                       "X-XSRF-Token": config['token']}
        
        client = client = tornado.httpclient.AsyncHTTPClient()
        vpc_url = "https://{}".format(config["vManage_ip"]) + "/dataservice/multicloud/accounts"
        vpc_request = tornado.httpclient.HTTPRequest(vpc_url, method="GET", headers=vpc_headers, validate_cert=False)
        try:
            vpc_response = await client.fetch(vpc_request)
            if vpc_response.code == 200:
                # self.write(vpc_response.body.decode("utf-8"))
                self.write(self.ResponseParse(vpc_response.body.decode("utf-8")))
        except tornado.httpclient.HTTPError as e:
            print(" Error:" + str(e))

        print(vpc_response.body.decode("utf-8"))
        # self.write(response) 

    def ResponseParse(self, res):
        if res:
            accounts = json.loads(res)["data"]

            final_res = {}
            count = 0
            for account in accounts:
                temp_res = {'name': account['accountName'],
                            'id': account['accountId'],
                            'provider': account['cloudType']}
                final_res[count] = temp_res
                count+=1
        return final_res
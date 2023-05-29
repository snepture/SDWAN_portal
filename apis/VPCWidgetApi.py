import tornado.web
import tornado.httpclient
import yaml
import asyncio
from module.Login_control import LoginControl

class UserBaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("username")

class VPCWidgetApi(UserBaseHandler):
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
        response = []
        ALL_Cloud = config['cloud_list']
        for vCloud in ALL_Cloud:
            vpc_url = "https://{}".format(config["vManage_ip"]) + "/dataservice/multicloud/widget/" + vCloud
            vpc_request = tornado.httpclient.HTTPRequest(vpc_url, method="GET", headers=vpc_headers, validate_cert=False)
            try:
                vpc_response = await client.fetch(vpc_request)
                if vpc_response.code == 200:
                    response.append(vpc_response.body.decode("utf-8"))
            except tornado.httpclient.HTTPError as e:
                print(vCloud + " Error:" + str(e))

        print(response)
        # self.write(response) 
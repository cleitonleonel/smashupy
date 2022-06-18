import os
import requests
import json
import re

URL_API = "https://br-game-api.t1tcp.com"
BASE_URL = "https://player.smashup.com"
URL_GAME = "https://br-game.t1tcp.com"


class Browser(object):

    def __init__(self):
        self.response = None
        self.headers = self.get_headers()
        self.session = requests.Session()

    def get_headers(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/87.0.4280.88 Safari/537.36"
        }
        return self.headers

    def send_request(self, method, url, **kwargs):
        response = self.session.request(method, url, **kwargs)
        if response.status_code in [401, 200]:
            return response
        return None


class SmashupAPI(Browser):

    def __init__(self, username, password):
        super().__init__()
        self.token = None
        self.referer = None
        self.username = username
        self.password = password

    def auth(self):
        data = {
            "referer": f"{BASE_URL}/iframe/auth/login",
            "username": self.username,
            "password": self.password
        }
        self.response = self.send_request("POST",
                                          BASE_URL + "/iframe/auth/login",
                                          data=data,
                                          headers=self.headers)
        return self.response

    def get_token(self):
        print("Gerando novo token...")
        self.auth()

        data = {
            'key': 'value'
        }
        self.response = self.send_request("GET",
                                          f"{BASE_URL}/player_center/goto_common_game/5928/crash",
                                          params=data,
                                          headers=self.headers)
        if self.response:
            self.token = re.findall(r"token=(.*?)&.*?", self.response.url)[0]
            self.save_token()
        return self.response

    def save_token(self):
        with open("smashup_token.json", "w") as file:
            file.write(json.dumps({"token": self.token}))

    def check_token(self):
        if not os.path.exists("smashup_token.json"):
            return self.get_token()
        with open("smashup_token.json", "r") as file:
            token = json.loads(file.read())
            self.token = token["token"]
            if self.get_profile().get("success", "is_success"):
                print("Token is valid!!!")
                return True
            print("Token not is valid!!!")
        return False

    def config_json(self):
        self.headers = self.get_headers()
        self.headers["referer"] = f"{URL_GAME}/mini/crash?token={self.token}&language=pt-BR"
        self.response = self.send_request("GET",
                                          f"{URL_GAME}/config.json",
                                          headers=self.headers)
        if self.response:
            return self.response.json()
        return False

    def get_profile(self):
        self.headers = self.get_headers()
        self.headers["x-auth-key"] = self.token
        self.response = self.send_request("GET",
                                          f"{URL_API}/mini/profile?",
                                          headers=self.headers)
        return self.response.json()

    def get_last_crashs(self, quantity=15):
        data = {
            "pagesize": quantity,
            "page": 1
        }
        self.headers = self.get_headers()
        self.headers["x-auth-key"] = self.token
        self.response = self.send_request("GET",
                                          f"{URL_API}/mini/crash/opencodes",
                                          params=data,
                                          headers=self.headers)
        return self.response.json()

    def get_last_doubles(self, quantity=15):
        data = {
            "pagesize": quantity,
            "page": 1
        }
        self.headers = self.get_headers()
        self.headers["x-auth-key"] = self.token
        self.response = self.send_request("GET",
                                          f"{URL_API}/mini/double/opencodes",
                                          params=data,
                                          headers=self.headers)
        return self.response.json()


if __name__ == '__main__':
    sa = SmashupAPI("user", "pass")
    if not sa.check_token():
        sa.get_token()

    result_crashs = {"items": [{"color": "preto" if i["point"] < 2 else "verde", "value": i["point"]}
                               for i in sa.get_last_crashs(quantity=12)["items"]]}
    print("CRASHS: ", json.dumps(result_crashs, indent=4))

    result_doubles = {"items": [{"color": i["color"], "value": i["number"]}
                                for i in sa.get_last_doubles(quantity=12)["items"]]}
    print("DOUBLES: ", json.dumps(result_doubles, indent=4))

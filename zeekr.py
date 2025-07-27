"""
极氪汽车签到脚本
"""

import base64
import random
import string
import time
import hashlib
from typing import Dict
from datetime import datetime

import requests
from requests.exceptions import RequestException
from config import FEISHU_WEBHOOK, JWT_TOKWN, DEVICE_ID, ACCOUNT_ID


class LarkNotify:

    def __init__(self, webhook: str):
        self.webhook = webhook

    def send_message(self, message: str):
        """发送消息"""
        if self.webhook == "":
            print(message)
            return

        payload = {
            "msg_type": "text",
            "content": {
                "text": message
            }
        }
        try:
            response = requests.post(self.webhook, json=payload)
            response.raise_for_status()
            print(message)
        except RequestException as e:
            print(f"发送消息失败: {e}")


class ZeekrHeader:
    """生成请求参数"""

    def __init__(self, headers: Dict[str, str] = {}):
        base_headers = {
            "Host": "api-gw-toc.zeekrlife.com",
            "AppId": "ONEX97FB91F061405",
            "Referer": "https://activity-h5.zeekrlife.com/",
            "Accept-Language": "zh-CN,zh-Hans;q=0.9",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": "https://activity-h5.zeekrlife.com",
            "device_id": DEVICE_ID,
            "risk_platform": "h5",
            "app_code": "toc_h5_green_zeekrapp",
            "Eagleeye-Sessionid": "",
            "Eagleeye-Traceid": "",
            "X-CORS-ONEX97FB91F061405-prod": "1",
            "Version": "2",
            "WorkspaceId": "prod",
            "platform": "",
            "app_type": "h5",
            "Authorization": f"Bearer {JWT_TOKWN}",
        }
        base_headers.update(headers)
        self.base_headers = base_headers

    def get_random_string(self, length: int) -> str:
        """生成指定长度的随机字符串"""
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        timestamp = int(time.time() * 1000)
        nonce = self.get_random_string(15)
        
        # 生成签名
        sign_str = "".join(sorted([
            "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCz09z6e9WOcNq+nUMX8Vq1Xe2EmJxuR3XbturefioF)E(Fl",
            nonce,
            str(timestamp),
        ]))
        sign_str = hashlib.sha1(sign_str.encode()).hexdigest()
        
        headers = self.base_headers.copy()
        headers.update({
            "x_ca_timestamp": str(timestamp),
            "x_ca_nonce": nonce,
            "x_ca_sign": sign_str,
            "x_ca_key": "H5-SIGN-SECRET-KEY",
            "riskTimeStamp": str(timestamp),
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) zeekr_iOS_v4.9.7",
        })
        return headers


class Zeekr:
    """极氪 APP 集碎片"""

    def __init__(self, lark_notify: LarkNotify):
        # 基础请求头
        self.header = ZeekrHeader()
        self.lark_notify = lark_notify

    def sign_in(self) -> None:
        """每日签到"""
        try:
            response = requests.post(
                "https://api-gw-toc.zeekrlife.com/zeekrlife-mp-val/toc/v1/zgreen/center",
                headers=self.header.get_headers(),
                json={},
            )
            response.raise_for_status()
            
            data = response.json()
            notify_message = ""
            if data["code"] == "000000":
                notify_message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 签到成功"

                tasks = data.get("data", {}).get("signInZgreenInfo", [])
                if len(tasks) > 0:
                    notify_message = f"{notify_message}\n\n完成任务："

                for task in tasks:
                    task_name = task.get("taskName", "")                
                    task_desc = task.get("desc", "")
                    notify_message = f"{notify_message}\n- {task_name}（{task_desc}）"
            else:
                notify_message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 签到失败: {data['msg']}"
        except Exception as e:
            notify_message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 签到失败: {e}"

        self.lark_notify.send_message(notify_message)

    def sync_day_walk_data(self) -> None:
        """更新微信步数"""
        step_count = random.randint(80000, 90000)
        secret = f"{step_count}_salt"
        for i in range(6):
            secret = base64.b64encode(secret.encode()).decode()
        
        data = {
            "stepCounts": step_count,
            "stepCountsSecret": secret,
            "sourceType": 30,
            "accountId": ACCOUNT_ID,
        }
        response = requests.post(
            "http://api-gw-toc.zeekrlife.com/zeekrlife-mp-val/v1/walkData/initDayWalkData",
            headers=self.header.get_headers(),
            json=data,
        )
        response.raise_for_status()
        resp_data = response.json()
        if resp_data.get("code") == "000000":
            notify_message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 更新微信步数成功: {step_count}"
        else:
            notify_message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 更新微信步数失败: {resp_data.get('msg')}"

        self.lark_notify.send_message(notify_message)

    def read_article(self) -> None:
        """每日阅读指定文章"""
        response = requests.get(
            "https://api-gw-toc.zeekrlife.com/zeekrlife-bbs-theme/v1/invitation/pub/detail?id=1927552810704109568",
            headers=self.header.get_headers(),
        )
        response.raise_for_status()
        resp_data = response.json()
        if resp_data.get("code") == "000000":
            notify_message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 阅读文章成功"
        else:
            notify_message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 阅读文章失败: {resp_data.get('msg')}"

        self.lark_notify.send_message(notify_message)

    def run(self) -> None:
        self.sign_in()
        self.sync_day_walk_data()
        self.read_article()


if __name__ == "__main__":
    lark_notify = LarkNotify(FEISHU_WEBHOOK)
    zeeker = Zeekr(lark_notify)
    zeeker.run() 
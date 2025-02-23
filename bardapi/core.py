import os
import random
import string
import requests
import json
import re


class Bard:
    def __init__(
        self, token=os.getenv("_BARD_API_KEY"), timeout=10, proxies=None, session=None
    ):
        """
        Initialize Bard

        :param token: (`str`, *optional*)
            Enter the __Secure-1PSID value. defaults to os.getenv("_BARD_API_KEY")
        :param timeout: (`int`, *optional*)
            Timeout in seconds when connecting bard server. The timeout is used on each request.
            defaults to 10 seconds.
        :param proxies: (`Dict[str, str]`, *optional*)
            A dictionary of proxy servers to use by protocol or endpoint, e.g., `{'http': 'foo.bar:3128',
            'http://hostname': 'foo.bar:4012'}`. The proxies are used on each request.
        :param session: (`requests.Session`, *optional*)
            An existing requests.Session object to be used for making HTTP requests.
        """
        headers = {
            "Host": "bard.google.com",
            "X-Same-Domain": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.114 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Origin": "https://bard.google.com",
            "Referer": "https://bard.google.com/",
        }
        self.token, self.proxies, self.timeout = token, proxies, timeout
        self._reqid = int("".join(random.choices(string.digits, k=4)))
        self.conversation_id = self.response_id = self.choice_id = ""
        self.session = requests.Session() if session is None else session
        self.session.headers = headers
        self.session.cookies.set("__Secure-1PSID", self.token)
        self.SNlM0e = self._get_snim0e()

    def _get_snim0e(self):
        if self.token and self.token[-1] != ".":
            raise Exception(
                "__Secure-1PSID value must end with a single dot. Enter correct __Secure-1PSID value."
            )
        elif not self.token:
            raise Exception("No token value entered.")
        resp = self.session.get(
            "https://bard.google.com/", timeout=self.timeout, proxies=self.proxies
        )
        if resp.status_code != 200:
            raise Exception(
                f"Response code not 200. \n - Try Bard on https://bard.google.com/ \n "
                f"- Check service area on https://support.google.com/bard/answer/13575153?hl=en. \n "
                f"- Response Status is {resp.status_code}"
            )
        snim0e = re.search(r"SNlM0e\":\"(.*?)\"", resp.text)
        if not snim0e:
            raise Exception(
                "SNlM0e value not found in response. Check __Secure-1PSID value."
            )
        return snim0e.group(1)

    def get_answer(self, input_text: str) -> dict:
        params = {
            "bl": "boq_assistant-bard-web-server_20230419.00_p1",
            "_reqid": str(self._reqid),
            "rt": "c",
        }
        input_text_struct = [
            [input_text],
            None,
            [self.conversation_id, self.response_id, self.choice_id],
        ]
        data = {
            "f.req": json.dumps([None, json.dumps(input_text_struct)]),
            "at": self.SNlM0e,
        }
        resp = self.session.post(
            "https://bard.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate",
            params=params,
            data=data,
            timeout=self.timeout,
            proxies=self.proxies,
        )
        resp_dict = json.loads(resp.content.splitlines()[3])[0][2]

        if not resp_dict:
            return {"content": f"Response Error: {resp.content}."}

        parsed_answer = json.loads(resp_dict)
        bard_answer = {
            "content": parsed_answer[0][0],
            "conversation_id": parsed_answer[1][0],
            "response_id": parsed_answer[1][1],
            "factualityQueries": parsed_answer[3],
            "textQuery": parsed_answer[2][0] if parsed_answer[2] else "",
            "choices": [{"id": i[0], "content": i[1]} for i in parsed_answer[4]],
        }
        self.conversation_id, self.response_id, self.choice_id = (
            bard_answer["conversation_id"],
            bard_answer["response_id"],
            bard_answer["choices"][0]["id"],
        )
        self._reqid += 100000

        return bard_answer

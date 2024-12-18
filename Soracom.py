"""
file     Soracom
time     2024-12-16
author   sayacom
email   
license  MIT License
"""

from hardware import *
import machine
import time
import network
import requests
from driver.simcom.common import AT_CMD
from driver.simcom.common import Modem


class Soracom:
    """
    note:
        en: Soracom
    details:
        color: '#34cdd7'
        link: https://github.com/sayacom
        image: ''
        category: Custom
    example: ''
    """

    def __init__(self, auth_type, username: str = "sora", password: str = "sora"):
        """
        label:
            en: Initialize %1 AuthType %2 Username %3 Password %4
        params:
            auth_type:
                name: auth_type
                field: dropdown
                options:
                    PAP: '''pap'''
                    CHAP: '''chap'''
                    none: '''none'''
            username:
                name: username
                type: str
                default: sora
            password:
                name: password
                type: str
                default: sora
        """
        self.ppp_username = username
        self.ppp_password = password

        self.ppp_authmode = 0
        if auth_type == "pap":
            self.ppp_authmode = 1
        elif auth_type == "chap":
            self.ppp_authmode = 2

        self.__modem = None
        self.__uart = None
        self.__ppp = None
        self.latest_response = None

    def set_interface(self, objs, obj_name: str = "catmgnss_0"):
        """
        label:
            en: '%1 Set UART/Modem Interface from %2 name %3'
        params:
            objs:
                name: objs
                field: dropdown
                options:
                    globals: globals()
            obj_name:
                name: obj_name
                type: str
                default: catmgnss_0
        """
        interface_definition = objs.get(obj_name, None)
        if interface_definition is None:
            print("Could not find interface.")
            return

        if isinstance(interface_definition, machine.UART):
            self.__uart = interface_definition
            self.__modem = Modem(self.__uart)
            print("Use UART")
        elif isinstance(interface_definition, Modem):
            self.__modem = interface_definition
            self.__uart = interface_definition.uart
            print("Use Modem")

    def set_debug_mode(self, debug_mode: bool = False):
        """
        label:
            en: '%1 Set debug mode %2'
        params:
            debug_mode:
                name: debug_mode
                type: bool
                default: 'False'
                field: switch
        """
        if self.__modem:
            self.__modem.modem_debug = debug_mode

    def execute_at_command(self, command: str, expect_response: str, timeout: int = 1000) -> None:
        """
        label:
            en: '%1 Execute AT Command %2 Expect response %3 Timeout %4'
        params:
            command:
                name: command
                type: str
            expect_response:
                name: expect_response
                type: str
            timeout:
                name: timeout
                type: int
                default: '1000'
                field: number
        """
        if self.__modem is None:
            return None

        output, error = self.__modem.execute_at_command(AT_CMD(f"{command}", expect_response, timeout))

        if not error:
            return output

        return None

    def dialup(self, phone_number: str = "*99#", timeout: int = 2000):
        """
        label:
            en: '%1 Dialup to %2 Timeout %3'
        params:
            phone_number:
                name: phone_number
                type: str
                default: '*99#'
            timeout:
                name: timeout
                type: int
                default: '100000'
                field: number
                max: '100'
                min: '0'
        """
        self.__modem.execute_at_command(AT_CMD(f"ATD{phone_number}", "CONNECT", timeout))

    def connect_ppp(self):
        """
        label:
            en: '%1 Connect PPP'
        """
        if self.__modem is None:
            return False

        self.__ppp = network.PPP(self.__uart)
        self.__ppp.active(True)

        for _ in range(5):
            self.__ppp.connect(authmode=self.ppp_authmode, username=self.ppp_username, password=self.ppp_password)
            time.sleep_ms(1000)
            if self.__ppp.isconnected():
                break

        return self.__ppp.isconnected()

    def ppp_isconnected(self):
        """
        label:
            en: '%1 PPP isConnected'
        """
        if self.__modem is None or self.__ppp is None:
            return False

        return self.__ppp.isconnected()

    def ppp_ifconfig(self):
        """
        label:
            en: '%1 PPP ifconfig'
        """
        if self.__modem is None or self.__ppp is None:
            return None

        return self.__ppp.ifconfig()

    def disconnect_ppp(self):
        """
        label:
            en: '%1 Disconnect PPP'
        """
        if self.__modem is None or self.__ppp is None:
            return False

        return self.__ppp.active(False)

    def send_data_by_http(self, dest, headers, body):
        """
        label:
            en: '%1 Send data as JSON by HTTP %2 Header %3 Body %4'
        params:
            dest:
                name: dest
                field: dropdown
                options:
                    Unified Endpoint: '''unified_endpoint'''
                    Harvest: '''harvest'''
                    Funnel: '''funnel'''
                    Funk: '''funk'''
            headers:
                name: headers
            body:
                name: body
        """
        host = None
        if dest == "unified_endpoint":
            host = "http://uni.soracom.io"
        elif dest == "harvest":
            host = "http://harvest.soracom.io"
        elif dest == "funnel":
            host = "http://funnel.soracom.io"
        elif dest == "funk":
            host = "http://funk.soracom.io"

        if headers == "":
            headers = None
        if body == "":
            body = None

        self.latest_response = requests.post(url=host, headers=headers, json=body)
        return self.latest_response

    def send_data_to_beam(self, endpoint_type, method, path, headers, body) -> None:
        """
        label:
            en: '%1 Send data as JSON by HTTP to SORACOM Beam, Endpoint %2 Method %3 Path
                %4 Headers %5 Body %6'
        params:
            endpoint_type:
                name: endpoint_type
                field: dropdown
                options:
                    HTTP: '''endpoint_http'''
                    Website: '''endpoint_website'''
            path:
                name: path
            headers:
                name: headers
            body:
                name: body
            method:
                name: method
        """
        if not path:
            path = "/"
        if not headers:
            headers = None
        if not body:
            body = None

        url = None
        if endpoint_type == "endpoint_http":
            url = f"http://beam.soracom.io:8888{path.lstrip('/')}"
        elif endpoint_type == "endpoint_website":
            url = f"http://beam.soracom.io:18080{path.lstrip('/')}"

        self.latest_response = requests.request(method=method, url=url, headers=headers, json=body)
        return self.latest_response

    def get_sim_tag(self, tag_name: str = "TAG_NAME"):
        """
        label:
            en: '%1 Get SIM Tag Name %2'
        params:
            tag_name:
                name: tag_name
                type: str
                default: TAG_NAME
        """
        self.latest_response = requests.get(url=f"http://metadata.soracom.io/v1/subscriber.tags.{tag_name}")
        return self.latest_response

    def set_sim_tag(self, tag_name: str = "TAG_NAME", tag_value: str = "TAG_VALUE"):
        """
        label:
            en: '%1 Set SIM Tag Name %2 Value %3'
        params:
            tag_name:
                name: tag_name
                type: str
                default: TAG_NAME
            tag_value:
                name: tag_value
                type: str
                default: TAG_VALUE
        """
        tag_object = [{"tagName": tag_name, "tagValue": tag_value}]
        self.latest_response = requests.put(url=f"http://metadata.soracom.io/v1/subscriber/tags", json=tag_object)
        return self.latest_response

    def delete_sim_tag(self, tag_name: str = "TAG_NAME"):
        """
        label:
            en: '%1 Delete SIM Tag Name %2'
        params:
            tag_name:
                name: tag_name
                type: str
                default: TAG_NAME
        """
        self.latest_response = requests.delete(url=f"http://metadata.soracom.io/v1/subscriber/tags/{tag_name}")
        return self.latest_response

    def get_userdata(self):
        """
        label:
            en: '%1 Get Userdata'
        """
        self.latest_response = requests.get(url=f"http://metadata.soracom.io/v1/userdata")
        return self.latest_response

    def get_latest_http_response_headers(self):
        """
        label:
            en: ' %1 Get latest HTTP response headers'
        """
        if self.latest_response is None:
            return None

        return self.latest_response.headers

    def get_latest_http_response_status_code(self):
        """
        label:
            en: '%1 Get latest HTTP response status code'
        """
        if self.latest_response is None:
            return None

        return self.latest_response.status_code

    def get_latest_http_response_text(self):
        """
        label:
            en: ' %1 Get latest HTTP response text'
        """
        if self.latest_response is None:
            return None

        return self.latest_response.text

    def get_latest_http_response_json(self):
        """
        label:
            en: ' %1 Get latest HTTP response JSON'
        """
        if self.latest_response is None:
            return None

        return self.latest_response.json()

    def get_latest_http_response_content(self):
        """
        label:
            en: ' %1 Get latest HTTP response content'
        """
        if self.latest_response is None:
            return None

        return self.latest_response.content

    def get_latest_http_response_reason(self):
        """
        label:
            en: ' %1 Get latest HTTP response reason'
        """
        if self.latest_response is None:
            return None

        return self.latest_response.reason

"""Define a client to interact with a RainMachine unit."""


import requests
from datetime import datetime
from controller import LocalController, RemoteController
from errors import RequestError, TokenExpiredError, raise_remote_error
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
#import urllib3
#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_LOCAL_PORT = 8080
DEFAULT_TIMEOUT = 30


def _raise_for_remote_status(url, data):
    """Raise an error from the remote API if necessary."""
    if data.get("errorType") and data["errorType"] > 0:
        raise_remote_error(data["errorType"])

    if data.get("statusCode") and data["statusCode"] != 200:
        raise RequestError(
            "Error requesting data from {}: {} {}".format(url, data['statusCode'], data['message'])
        )


class Client:
    """Define the client."""

    def __init__(self, request_timeout=DEFAULT_TIMEOUT):
        """Initialize."""
        self.controllers = {}
        self.request_timeout = request_timeout

    def load_local(self, host, password, port=DEFAULT_LOCAL_PORT, ssl=False, skip_existing=False):
        """Create a local client."""
        controller = LocalController(self.request, host, port, ssl)
        controller.login(password)

        wifi_data = controller.provisioning.wifi()
        mac_address = wifi_data["macAddress"].upper()  # fix lower case from local mac address

        if skip_existing and mac_address in self.controllers:
            return
        controller.mac = mac_address
        controller.name = controller.provisioning.device_name
        version_data = controller.provisioning.versions()
        controller.api_version = version_data["apiVer"]
        controller.hardware_version = version_data["hwVer"]
        controller.software_version = version_data["swVer"]

        self.controllers[controller.mac] = controller

    def load_remote(self, email, password, skip_existing=False):
        """Create a remote client."""
        auth_resp = self.request(
            "post",
            "https://my.rainmachine.com/login/auth",
            json={"user": {"email": email, "pwd": password, "remember": 1}},
        )

        access_token = auth_resp['access_token']
        sprinklers_resp = self.request(
            "post",
            "https://my.rainmachine.com/devices/get-sprinklers",
            access_token=access_token,
            json={"user": {"email": email, "pwd": password, "remember": 1}},
        )

        for sprinkler in sprinklers_resp["sprinklers"]:
            if skip_existing and sprinkler["mac"] in self.controllers:
                continue

            controller = RemoteController(self.request)
            controller.login(access_token, sprinkler["sprinklerId"], password)

            controller.mac = sprinkler["mac"]
            controller.name = sprinkler["name"]
            self.controllers[sprinkler["mac"]] = controller
            version_data = controller.provisioning.versions()
            controller.api_version = version_data["apiVer"]
            controller.hardware_version = version_data["hwVer"]
            controller.software_version = version_data["swVer"]

    def request(self, method, url, access_token=None, access_token_expiration=None, ssl=True, **kwargs):
        """Make a request against the RainMachine device."""
        if access_token_expiration and datetime.now() >= access_token_expiration:
            raise TokenExpiredError("Long-lived access token has expired")

        kwargs.setdefault('headers', {"Content-Type": "application/json"})
        if access_token:
            kwargs.setdefault('params', {})['access_token'] = access_token

        try:
            resp = requests.request(method, url, verify=ssl, timeout=DEFAULT_TIMEOUT, **kwargs)
            resp.raise_for_status()
            data = resp.json()
            _raise_for_remote_status(url, data)
        except requests.exceptions.HTTPError:
            raise TokenExpiredError("Long-lived access token has expired")
        except requests.exceptions.Timeout:
            raise RequestError("HTTP error occurred using url: {}".format(url))
        return data

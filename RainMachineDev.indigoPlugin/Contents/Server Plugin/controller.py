"""Define a RainMachine controller class."""


from datetime import datetime, timedelta

from program import Program
from provision import Provision
from zone import Zone
from watering import Watering

URL_BASE_LOCAL = 'https://{}:{}/api/4'
URL_BASE_REMOTE = 'https://api.rainmachine.com/{}/api/4'


class Controller:  # pylint: disable=too-many-instance-attributes
    """Define the controller."""

    def __init__(self, request):
        """Initialize."""
        self._access_token = None
        self._access_token_expiration = None
        self._client_request = request
        self._host = None
        self._ssl = True
        self.api_version = None
        self.hardware_version = None
        self.mac = None
        self.name = None
        self.software_version = None
        self.connection_type = None

        # API endpoints:
        self.programs = Program(self._request)
        self.provisioning = Provision(self._request)
        self.zones = Zone(self._request)
        self.watering = Watering(self._request)

    def _request(self, method, endpoint, **kwargs):
        """Wrap the generic request method to add access token, etc."""
        return self._client_request(
            method,
            '{}/{}'.format(self._host, endpoint),
            access_token=self._access_token,
            access_token_expiration=self._access_token_expiration,
            ssl=self._ssl,
            **kwargs
        )


class LocalController(Controller):
    """Define a controller accessed over the LAN."""

    def __init__(self, request, host, port, ssl):
        """Initialize."""
        Controller.__init__(self, request)

        self._host = URL_BASE_LOCAL.format(host, port)
        self._ssl = ssl
        self.connection_type = "local"

    def login(self, password):
        auth_resp = self._client_request(
            "POST",
            "{}/auth/login".format(self._host),
            json={"pwd": password, "remember": 1},
            ssl=False)
        self._access_token = auth_resp['access_token']
        self._access_token_expiration = datetime.now() + timedelta(seconds=int(auth_resp["expires_in"]) - 10)


class RemoteController(Controller):
    """Define a controller accessed over RainMachine's cloud."""

    def login(self, stage_1_access_token, sprinkler_id, password):
        """Authenticate against the device (remotely)."""
        auth_resp = self._client_request(
            "post",
            "https://my.rainmachine.com/devices/login-sprinkler",
            access_token=stage_1_access_token,
            json={"sprinklerId": sprinkler_id, "pwd": password})
        self._access_token = auth_resp['access_token']
        self._host = URL_BASE_REMOTE.format(sprinkler_id)
        self.connection_type = "cloud"

"""Define an object to interact with provisioning info."""


class Provision:
    """Define a provisioning object."""

    def __init__(self, request):
        """Initialize."""
        self._request = request

    @property
    def device_name(self):
        """Get the name of the device."""
        data = self._request("get", "provision/name")
        return data["name"]

    def settings(self):
        """Get a multitude of settings info."""
        return self._request("get", "provision")

    def wifi(self):
        """Get MAC and wifi info from the device."""
        return self._request("get", "provision/wifi")

    def versions(self):
        """Get software, hardware, and API versions."""
        return self._request("get", "apiVer")

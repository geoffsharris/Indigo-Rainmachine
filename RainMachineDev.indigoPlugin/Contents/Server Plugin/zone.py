"""Define an object to interact with zones."""


class Zone:
    """Define a zone object."""

    def __init__(self, request):
        """Initialize."""
        self._request = request

    def start(self, zone_id, time):
        """Start a zone for a duration of time."""
        return self._request("post", "zone/{}/start".format(zone_id), json={"time": time})

    def stop(self, zone_id):
        """Stop a zone."""
        return self._request("post", "zone/{}/stop".format(zone_id))

    def all(self):
        """Return list of all zones."""
        return self._request("get", "zone")

    def get(self, zone_id):
        """Return a specific zone."""
        return self._request("get", "zone/{}".format(zone_id))


"""Define an object to interact with watering."""


class Watering:
    """Define a watering object."""

    def __init__(self, request):
        """Initialize."""
        self._request = request

    def pause_all(self, seconds):
        """Pause all watering for a specified number of seconds."""
        return self._request("post", "watering/pauseall", json={"duration": seconds})

    def queue(self):
        """Return the queue of active watering activities."""
        data = self._request("get", "watering/queue")
        return data["queue"]

    def stop_all(self):
        """Stop all programs and zones from running."""
        return self._request("post", "watering/stopall")

    def unpause_all(self):
        """Unpause all paused watering."""
        return self.pause_all(0)

    def zone(self):
        """Return the queue of active watering activities."""
        return self._request("get", "watering/zone")

    def program(self):
        """Return the queue of active watering activities."""
        return self._request("get", "watering/program")

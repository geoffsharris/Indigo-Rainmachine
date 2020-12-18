"""Define an object to interact with programs."""


class Program:
    """Define a program object."""

    def __init__(self, request):
        """Initialize."""
        self._request = request

    def all(self):
        """Return all programs on a controller."""
        return self._request("get", "program")

    def get(self, program_id):
        """Return a specific program."""
        return self._request("get", "program/{}".format(program_id))

    def start(self, program_id):
        """Start a program."""
        return self._request("post", "program/{}/start".format(program_id))

    def stop(self, program_id):
        """Stop a program."""
        return self._request("post", "program/{}/stop".format(program_id))

class ParameterNotFound(Exception):
    """Error raised when a parameter in an instrument is not found."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"ParameterNotFound: {self.message}"

class InvalidInput(Exception):
    def __init__(self, message: str = "请求参数校验失败", *, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFound(Exception):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message)
        self.message = message


class RateLimited(Exception):
    def __init__(self, message: str = "请求过于频繁，请稍后重试"):
        super().__init__(message)
        self.message = message


class Timeout(Exception):
    def __init__(self, message: str = "请求超时，请稍后重试"):
        super().__init__(message)
        self.message = message


class DependencyUnavailable(Exception):
    def __init__(self, message: str = "外部依赖不可用，请稍后重试"):
        super().__init__(message)
        self.message = message





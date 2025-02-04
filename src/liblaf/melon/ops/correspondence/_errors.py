class InvalidNormalThresholdError(ValueError):
    normal_threshold: float

    def __init__(self, normal_threshold: float) -> None:
        self.normal_threshold = normal_threshold
        msg: str = f"Invalid normal threshold: {normal_threshold}\n"
        msg += "Normal threshold must be in the range [-1.0, 1.0]"
        super().__init__(msg)

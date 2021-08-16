class ConversionUtils:
    @staticmethod
    def duration_to_seconds(duration):
        unit = duration[-1]
        if unit == "s":
            unit = 1
        elif unit == "m":
            unit = 60
        elif unit == "h":
            unit = 3600

        return int(duration[:-1]) * unit

import logging

from ....._utils import DataclassLoggerAdapter, LoggingContext, log_on_exception
from ._constants import Constants, FacilityCode, FacilityPrefix

_base_logger = logging.getLogger(__name__)
_ctx = LoggingContext(
    rice_id=Constants.RICE_ID,
    object=LoggingContext.Object.WORK_ORDER.value,
)
logger = DataclassLoggerAdapter(_base_logger, _ctx)


class FacilityDetectorError(Exception):
    pass


class FacilityDetector:
    """
    Determines facility from filename prefix.
    """

    @log_on_exception(logger)
    def __call__(self, filename: str) -> FacilityCode:
        if not filename:
            raise FacilityDetectorError("Filename is required")

        try:
            prefix_str = filename[:2].upper()
            prefix = FacilityPrefix.from_string(prefix_str)
            facility_code = prefix.to_facility_code()
            logger.info(
                f"Detected facility '{facility_code.value}' "
                f"from filename prefix '{prefix_str}'"
            )
            return facility_code

        except Exception as unexpected_error:
            raise FacilityDetectorError(
                f"Failed to detect facility from filename '{filename}': {str(unexpected_error)}"
            ) from unexpected_error

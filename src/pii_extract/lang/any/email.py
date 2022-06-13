"""
Detection of email addresses
"""

from pii_data.types import PiiEnum


_EMAIL_PATTERN = r"[\w\.=-]+ @ [\w\.-]+ \. [\w]{2,3}"


PII_TASKS = [(PiiEnum.EMAIL_ADDRESS, _EMAIL_PATTERN, "Email address")]

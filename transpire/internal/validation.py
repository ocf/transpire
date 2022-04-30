import re

DNSNAME_REGEX = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")


def is_valid_dnsname(name: str) -> bool:
    return DNSNAME_REGEX.match(name) is not None

import re

from django import template

register = template.Library()


@register.filter
def count_steps(value):
    """Брой редове с номерирана стъпка, например „1. Провери периода.“."""
    count = 0
    for line in str(value or "").splitlines():
        if re.match(r"^\s*\d+[.)]\s+\S", line):
            count += 1
    return count

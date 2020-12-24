from django.template.defaultfilters import stringfilter

from . import register


@register.filter
@stringfilter
def suffix(s: str, by="/"):
    return s.split(by)[-1]

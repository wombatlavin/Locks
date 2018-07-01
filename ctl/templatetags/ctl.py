import datetime

from django import template

register = template.Library()

@register.filter(name='change_date')
def change_date(myDate, days):
    return myDate + datetime.timedelta(days=days)

@register.filter(name='pence')
def pence(num):
    return int(num*100)

@register.filter(name='item_count')
def job_item_count(job, item):
    return job.item_count(item)

@register.filter(name='counter')
def counter(stars):
    result = ''
    for x in range(stars):
        result = result+'x'
    return result
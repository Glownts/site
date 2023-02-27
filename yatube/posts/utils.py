from django.core.paginator import Paginator
from django.conf import settings


def paginator(request, items):
    paginator = Paginator(items, settings.POSTS_PER_PAGE_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj

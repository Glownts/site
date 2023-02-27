from django.core import paginator


def pagination(self, posts):
    page = self.request.GET.get("page")
    pagination = paginator.Paginator(posts, self.paginate_by)
    try:
        page_obj = pagination.page(page)
    except (paginator.PageNotAnInteger, paginator.EmptyPage):
        page_obj = pagination.page(1)
    return page_obj

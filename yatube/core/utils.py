from django.core.paginator import Paginator


def get_page_obj(query_set, rec_on_page, request):
    paginator = Paginator(query_set, rec_on_page)
    page_namber = request.GET.get('page')
    return paginator.get_page(page_namber)

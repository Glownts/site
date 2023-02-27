from datetime import datetime


def year(request):
    '''Дата в футере страницы'''
    return {
        'year': datetime.now().year
    }

from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    '''Обработка статической страницы "Технологии"'''
    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    '''Обработка статической страницы "Об авторе"'''
    template_name = 'about/tech.html'

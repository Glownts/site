from django.test import TestCase, Client


class CoreTests(TestCase):
    '''Тестирование view-функций приложения posts.'''

    def setUp(cls):
        '''Создание гостевого клиента.'''
        cls.guest = Client()

    def test_posts_correct_templates(self):
        '''Тест на использование верных шаблонов.'''
        self.assertTemplateUsed(self.guest.get('/random_URL'), 'core/404.html')

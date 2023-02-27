from django.test import TestCase, Client
from http import HTTPStatus


class StaticPagesURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

    def test_about_URL_exist(self):
        '''Тест на доступность URL-адреса'''
        expected_value = HTTPStatus.OK
        responses = (
            '/about/author/',
            '/about/tech/',
        )
        for value in responses:
            with self.subTest(value):
                self.assertEqual(
                    StaticPagesURLTests.guest_client.get(value).status_code,
                    expected_value,
                    'Искомый URL-адрес недоступен'
                )

    def test_about_template_for_URL_exist(self):
        '''Тест на шаблон для URL-адреса'''
        responses = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for value, expected_value in responses.items():
            with self.subTest(field=value):
                self.assertTemplateUsed(
                    StaticPagesURLTests.guest_client.get(value),
                    expected_value,
                    'Ошибка запроса HTML-шаблона'
                )

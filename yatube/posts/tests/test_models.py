from django.test import TestCase


from posts.models import Group, Post, User


class PostsModelsTests(TestCase):
    '''Тестирование моделей приложения posts.'''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст записи',
        )

    def test_models_str_name(self):
        '''Тест на корректность работы __str__.'''
        strings = {
            str(PostsModelsTests.post): 'Тестовый текст ',
            str(PostsModelsTests.group): 'Тестовая группа',
        }

        for value, expected_value in strings.items():
            with self.subTest(field=value):
                self.assertEqual(
                    value,
                    expected_value,
                    'Метод __str__ работает некорректно'
                )

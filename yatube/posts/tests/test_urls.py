from django.test import TestCase, Client
from django.core.cache import cache


from http import HTTPStatus


from posts.models import Follow, Group, Post, User


class PostsURLsTests(TestCase):
    '''Тестирование URL приложения posts.'''

    @classmethod
    def setUpClass(cls):
        '''
        Создание гостя, авторизированного пользователя,
        автора записи, тестовой группы и записи.
        '''
        super().setUpClass()

        # Создаем неавторизированного пользователя
        cls.guest_client = Client()

        # Создаем пользователя и авторизируем его
        cls.user = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        # Создаем автора записи и авторизируем его
        cls.author = User.objects.create_user(username='author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        # Создаем экземпляр группы и записи
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст записи',
            id=1,
        )
        Follow.objects.create(
            user=cls.user,
            author=cls.author
        )

    def setUp(self):
        cache.clear()

    def test_posts_URL_exist_all(self):
        '''Тест доступа адресов неавторизированному пользователю.'''
        responses_get = (
            (
                '/',
                PostsURLsTests.guest_client,
                False,
                HTTPStatus.OK
            ),
            (
                f'/group/{PostsURLsTests.group.slug}/',
                PostsURLsTests.guest_client,
                False,
                HTTPStatus.OK
            ),
            (
                f'/profile/{PostsURLsTests.user.username}/',
                PostsURLsTests.guest_client,
                False,
                HTTPStatus.OK
            ),
            (
                f'/posts/{PostsURLsTests.post.id}/',
                PostsURLsTests.guest_client,
                False,
                HTTPStatus.OK
            ),
            (
                '/create/',
                PostsURLsTests.guest_client,
                False,
                HTTPStatus.FOUND
            ),
            (
                f'/posts/{PostsURLsTests.post.id}/edit/',
                PostsURLsTests.guest_client,
                False,
                HTTPStatus.FOUND
            ),
            (
                f'/profile/{PostsURLsTests.author.username}/unfollow/',
                PostsURLsTests.guest_client,
                False,
                HTTPStatus.FOUND
            ),
            (
                f'/profile/{PostsURLsTests.author.username}/follow/',
                PostsURLsTests.guest_client,
                False,
                HTTPStatus.FOUND
            ),
            (
                '/create/',
                PostsURLsTests.authorized_client,
                False,
                HTTPStatus.OK
            ),
            (
                f'/posts/{PostsURLsTests.post.id}/edit/',
                PostsURLsTests.authorized_client,
                False,
                HTTPStatus.FOUND
            ),
            (
                f'/profile/{PostsURLsTests.author.username}/unfollow/',
                PostsURLsTests.authorized_client,
                True,
                HTTPStatus.OK
            ),
            (
                f'/profile/{PostsURLsTests.author.username}/follow/',
                PostsURLsTests.authorized_client,
                True,
                HTTPStatus.OK
            ),
            (
                f'/posts/{PostsURLsTests.post.id}/edit/',
                PostsURLsTests.author_client,
                False,
                HTTPStatus.OK
            ),
            (
                '/posts/strange_URL/',  # Неизвестный адрес
                PostsURLsTests.author_client,
                False,
                HTTPStatus.NOT_FOUND
            ),
        )
        responses_post = (
            (
                '/create/',
                PostsURLsTests.authorized_client,
                False,
                HTTPStatus.OK
            ),
            (
                f'/posts/{PostsURLsTests.post.id}/edit/',
                PostsURLsTests.authorized_client,
                False,
                HTTPStatus.FOUND
            ),
            (
                f'/posts/{PostsURLsTests.post.id}/comment/',
                PostsURLsTests.guest_client,
                False,
                HTTPStatus.FOUND
            ),
            (
                f'/posts/{PostsURLsTests.post.id}/comment/',
                PostsURLsTests.authorized_client,
                True,
                HTTPStatus.OK
            ),
        )

        for url, client, follow, status in responses_get:
            with self.subTest(url=url, client=client, follow=follow):
                self.assertEqual(
                    client.get(url, follow=follow).status_code,
                    status,
                    ('Ошибка доступа URL адреса')
                )

        for url, client, data, status in responses_post:
            with self.subTest(url=url, client=client, data=data):
                form_data = {
                    'text': 'Тестовый комментарий'
                }
                if data is False:
                    self.assertEqual(
                        client.post(url).status_code,
                        status,
                        ('Ошибка доступа URL адреса')
                    )
                else:
                    self.assertEqual(
                        client.post(
                            url,
                            data=form_data,
                            follow=True
                        ).status_code,
                        status,
                        ('Ошибка доступа URL адреса')
                    )

    def test_posts_URL_redirect_unauthorized(self):
        '''Тест переадресации неавторизированных пользователей.'''
        responses = {
            '/create/':
                '/auth/login/?next=/create/',
            f'/posts/{PostsURLsTests.post.id}/edit/':
                f'/auth/login/?next=/posts/{PostsURLsTests.post.id}/edit/',
        }

        for value, expected_value in responses.items():
            with self.subTest(field=value):
                self.assertRedirects(
                    PostsURLsTests.guest_client.get(value, follow=True),
                    expected_value
                )

    def test_posts_template_for_URL_exist(self):
        '''Тест шаблонов вызываемых для адресов.'''
        responses = {
            '/':
                'posts/index.html',
            f'/group/{PostsURLsTests.group.slug}/':
                'posts/group_list.html',
            f'/profile/{PostsURLsTests.author.username}/':
                'posts/profile.html',
            f'/posts/{PostsURLsTests.post.id}/':
                'posts/post_detail.html',
            f'/posts/{PostsURLsTests.post.id}/edit/':
                'posts/post_create.html',
            '/create/':
                'posts/post_create.html',
        }

        for value, expected_value in responses.items():
            with self.subTest(value=value):
                self.assertTemplateUsed(
                    PostsURLsTests.author_client.get(value),
                    expected_value,
                    'Ошибка запроса HTML-шаблона'
                )

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django import forms

import shutil
import tempfile

from time import sleep


from posts.models import Follow, Group, Post, Comment, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    '''Тестирование view-функций приложения posts.'''

    @classmethod
    def setUpClass(cls):
        '''
        Создание авторизированного пользователя,
        тестовой группы и записи.
        '''
        super().setUpClass()

        # Создаем пользователя и авторизируем его
        cls.user = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        # Создаем неавторизированного автора
        cls.author = User.objects.create(username='author')

        # Создаем экземпляр группы
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        # Создаем n + 2 тестовых записей
        cls.posts = []
        number_of_posts = settings.POSTS_PER_PAGE_LIMIT + 2
        for count in range(number_of_posts):
            cls.posts.append(
                Post.objects.create(
                    author=cls.user,
                    text=f'Запись {count}',
                    group=cls.group,
                )
            )
            sleep(0.01)

        # Создаем картинку для тестов
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        test_image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        # Создаем запись с картинкой
        cls.full_post = Post.objects.create(
            author=PostsViewsTests.user,
            text='Текст записи с картинкой',
            group=PostsViewsTests.group,
            image=test_image,
        )
        # Создаем комментарий
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            author=PostsViewsTests.user,
            post_id=PostsViewsTests.full_post.id
        )

    def setUp(self):
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_posts_uploaded_files(self):
        test_file = SimpleUploadedFile(
            name='small.aac',
            content=b'\x47\x49\x46\x38\x39\x61\x02\x00',
            content_type='audio/aac'
        )
        form_data = {
            'text': 'Новая запись',
            'author': PostsViewsTests.user.id,
            'image': test_file,
        }
        response = PostsViewsTests.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertFormError(
            response,
            'form',
            'image',
            'Загрузите правильное изображение.'
            + ' Файл, который вы загрузили,'
            + ' поврежден или не является изображением.'
        )

    def test_posts_correct_templates(self):
        '''Тест на использование верных шаблонов.'''
        templates_pages_names = {
            reverse(
                'posts:index'
            ): 'posts/index.html',
            reverse(
                'posts:post_create'
            ): 'posts/post_create.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostsViewsTests.posts[1].id}
            ): 'posts/post_create.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsViewsTests.posts[1].id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': PostsViewsTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostsViewsTests.user.username}
            ): 'posts/profile.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertTemplateUsed(
                    PostsViewsTests.authorized_client.get(reverse_name),
                    template
                )

    def test_posts_paginator(self):
        '''Тест работы паджинатора на первой и второй страницах.'''
        reverses = (
            reverse(
                'posts:index'
            ),
            reverse(
                'posts:group_list',
                kwargs={'slug': PostsViewsTests.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostsViewsTests.user.username}
            ),
        )
        # Тест первой страницы
        for reverse_name in reverses:
            with self.subTest(reverse_name=reverse_name):
                response = PostsViewsTests.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POSTS_PER_PAGE_LIMIT
                )
        # Тест второй страницы
        for reverse_name in reverses:
            with self.subTest(reverse_name=reverse_name):
                response = PostsViewsTests.authorized_client.get(
                    reverse_name + '?page=2'
                )
                self.assertEqual(len(response.context['page_obj']), 3)

    def test_posts_context(self):
        """Тест контекста в шаблонах index, group_list и profile."""
        reverses = (
            reverse(
                'posts:index'
            ),
            reverse(
                'posts:group_list',
                kwargs={'slug': PostsViewsTests.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostsViewsTests.user.username}
            ),
        )

        for reverse_name in reverses:
            with self.subTest(reverse_name=reverse_name):
                response = PostsViewsTests.authorized_client.get(reverse_name)
                # Запрашиваем запись с картинкой, т.к. она создалась последней
                test_object = response.context['page_obj'][0]

                self.assertEqual(
                    test_object.text,
                    PostsViewsTests.full_post.text
                )
                self.assertEqual(
                    test_object.group.title,
                    PostsViewsTests.full_post.group.title
                )
                self.assertEqual(
                    test_object.author.username,
                    PostsViewsTests.full_post.author.username
                )
                self.assertEqual(
                    test_object.image,
                    PostsViewsTests.full_post.image
                )

    def test_posts_context_post_detail(self):
        '''Тест контекста в шаблоне post_detail.'''
        reverse_name = reverse(
            'posts:post_detail',
            kwargs={'post_id': PostsViewsTests.full_post.id}
        )
        response = PostsViewsTests.authorized_client.get(reverse_name)
        test_object_1 = response.context.get('post')
        test_object_2 = response.context.get('comments')

        self.assertEqual(
            test_object_1.text,
            PostsViewsTests.full_post.text
        )
        self.assertEqual(
            test_object_1.group.title,
            PostsViewsTests.full_post.group.title
        )
        self.assertEqual(
            test_object_1.author.username,
            PostsViewsTests.full_post.author.username
        )
        self.assertEqual(
            test_object_1.image,
            PostsViewsTests.full_post.image
        )
        self.assertEqual(
            test_object_2[0].text,
            PostsViewsTests.comment.text
        )

    def test_posts_context_creation_form(self):
        """
        Тест контекста в шаблоне post_create/post_edit.
        Проверка типов данных полей форм.
        """
        reverses = (
            reverse(
                'posts:post_create'
            ),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostsViewsTests.posts[1].id}
            ),
        )
        for reverse_name in reverses:
            response = PostsViewsTests.authorized_client.get(reverse_name)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_posts_post_in_right_places(self):
        '''Тест размещения записи на страницах при ее создании.'''
        # Создаем другую группу
        self.new_group = Group.objects.create(
            title='Новая тестовая группа',
            slug='new_test_slug',
            description='Новое тестовое описание',
        )
        # создаем пост, принадлежщий другой группе
        self.post = Post.objects.create(
            author=PostsViewsTests.user,
            text='Текст записи другой группы',
            group=self.new_group
        )
        reverses = (
            reverse(
                'posts:index'
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostsViewsTests.user.username}
            ),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.new_group.slug}
            ),
        )
        # Проверяем, что пост в нужных местах
        for reverse_name in reverses:
            response = self.authorized_client.get(reverse_name)
            # Новый пост будет нулевым объектом page_obj
            test_object = response.context['page_obj'][0]

            self.assertEqual(
                test_object.text,
                self.post.text
            )
            self.assertEqual(
                test_object.group.title,
                self.post.group.title
            )
            self.assertEqual(
                test_object.author.username,
                self.post.author.username
            )

    def test_posts_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        # Посылаем запрос, тем самым кэшируя страницу
        response = self.authorized_client.get(reverse('posts:index'))
        check_1 = response.content
        # Удаляем все посты
        Post.objects.all().delete()
        # Посылаем второй запрос и получаем результат из кэша
        response = self.authorized_client.get(reverse('posts:index'))
        check_2 = response.content
        # Очищаем кэш
        cache.clear()
        # Посылаем третий запрос и получаем ответ без постов
        response = self.authorized_client.get(reverse('posts:index'))
        check_3 = response.content

        self.assertEqual(check_1, check_2)
        self.assertNotEqual(check_2, check_3)

    def test_posts_follow(self):
        '''Проверка функции подписки/отписки.'''
        reverses = {
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostsViewsTests.author.username}
            ): True,
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': PostsViewsTests.author.username}
            ): False,
        }

        for value, expected_value in reverses.items():
            with self.subTest(value=value):
                PostsViewsTests.authorized_client.get(value)
                # Если подписка есть, exists() вернет True, иначе False
                self.assertEqual(
                    Follow.objects.filter(
                        user=PostsViewsTests.user,
                        author=PostsViewsTests.author
                    ).exists(),
                    expected_value
                )

    def test_posts_feed(self):
        '''Проверка ленты подписок.'''
        reverses = (
            reverse(
                'posts:follow_index'
            ),
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostsViewsTests.author.username}
            ),
        )
        # Создали пост автора
        Post.objects.create(
            text='Авторский контент',
            author=PostsViewsTests.author
        )
        # Перешли на feed и увидели, что до подписки он пустой
        response = PostsViewsTests.authorized_client.get(
            reverses[0]
        ).context['page_obj']
        self.assertEqual(len(response), 0)
        # Подписались
        PostsViewsTests.authorized_client.get(reverses[1])
        # Проверили, что пост автора появлися в feed
        response = PostsViewsTests.authorized_client.get(
            reverses[0]
        ).context['page_obj']
        self.assertEqual(len(response), 1)

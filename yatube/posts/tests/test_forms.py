from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.conf import settings
from django.urls import reverse


import shutil
import tempfile


from posts.models import Group, Post, Comment, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTests(TestCase):
    '''Тестируем форм приложения posts.'''

    @classmethod
    def setUpClass(cls):
        '''
        Создание авторизированного пользователя,
        тестовой группы и записи.
        '''
        super().setUpClass()
        # Создаем гостя
        cls.guest = Client()
        # Создаем авторизированного пользователя и запись
        cls.user = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        # Создаем экземпляр группы
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test_slug_1',
            description='Тестовое описание 1',
        )
        # Создаем изначальную запись
        cls.start_post = Post.objects.create(
            text='Стартовая запись',
            author=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_posts_post_create(self):
        """Тест создания записи валидной формой."""
        posts_count = Post.objects.count()
        # Создаем картинку для теста
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
        # Заполняем поля формы
        form_data = {
            'text': 'Новая запись',
            'group': PostsFormsTests.group.id,
            'author': PostsFormsTests.user.id,
            'image': test_image,
        }
        # Отправляем POST-запрос
        response_post = PostsFormsTests.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.new_post = Post.objects.get(
            text='Новая запись',
            group=PostsFormsTests.group,
            author=PostsFormsTests.user,
            image='posts/small.gif',
        )
        # Проверяем создание поста и редирект
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(self.new_post.text, 'Новая запись')
        self.assertRedirects(
            response_post,
            reverse(
                'posts:profile',
                kwargs={'username': PostsFormsTests.user.username}
            )
        )

    def test_posts_uploaded_files(self):
        test_file = SimpleUploadedFile(
            name='small.aac',
            content=b'\x47\x49\x46\x38\x39\x61\x02\x00',
            content_type='audio/aac'
        )
        form_data = {
            'text': 'Новая запись',
            'author': PostsFormsTests.user.id,
            'image': test_file,
        }
        response = PostsFormsTests.authorized_client.post(
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

    def test_posts_post_edit(self):
        """Тест изменения записи валидной формой."""
        # Заполняем поля формы, изменяя запись
        form_data = {
            'text': 'Измененная запись',
            'group': PostsFormsTests.group.id
        }
        # Отправляем POST-запрос
        response = PostsFormsTests.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostsFormsTests.start_post.id}
            ),
            data=form_data,
            follow=True
        )
        # Проверяем, что текст записи изменился
        self.edited_post = Post.objects.get(id=PostsFormsTests.start_post.id)
        self.assertTrue(
            (self.edited_post.text, self.edited_post.group),
            ('Измененная запись', PostsFormsTests.group.id)
        )
        # Проверяем редирект
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.edited_post.id}
            )
        )

    def test_posts_comment(self):
        """Тест создания комментария."""
        # Заполняем поля формы
        form_data = {
            'text': 'Комментарий',
            'post': PostsFormsTests.start_post.id,
            'author': PostsFormsTests.user.id,
        }
        # Отправляем POST-запрос гостем
        PostsFormsTests.guest.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.start_post.id}
            ),
            data=form_data,
            follow=True
        )
        # Проверяем отсутствие комментария
        self.assertEqual(Comment.objects.count(), 0)
        # Отправляем POST-запрос авторизированным клиентом
        PostsFormsTests.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.start_post.id}
            ),
            data=form_data,
            follow=True
        )
        self.comment = Comment.objects.get(
            post=PostsFormsTests.start_post.id,
        )
        # Проверяем, что комментарий появился
        self.assertEqual(self.comment.text, 'Комментарий')

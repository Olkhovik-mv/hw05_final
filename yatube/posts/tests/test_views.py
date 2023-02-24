import shutil
import tempfile
from datetime import datetime, timedelta

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

POST_ID = 1

USERNAME = 'username_1'
USERNAME_2 = 'username_2'
GROUP_SLUG = 'slug_group_1'
GROUP_2_SLUG = 'slug_group_2'
PAGE_2 = '?page=2'

INDEX_URL = reverse('posts:index')
GROUP_LIST_URL = reverse('posts:group_list', kwargs={'slug': GROUP_SLUG})
GROUP_2_LIST_URL = reverse('posts:group_list', kwargs={'slug': GROUP_2_SLUG})
PROFILE_URL = reverse('posts:profile', kwargs={'username': USERNAME})
PROFILE_2_URL = reverse('posts:profile', kwargs={'username': USERNAME_2})
DETAIL_URL = reverse('posts:post_detail', kwargs={'post_id': POST_ID})
CREATE_URL = reverse('posts:post_create')
EDIT_URL = reverse('posts:post_edit', kwargs={'post_id': POST_ID})
FOLLOW_INDEX_URL = reverse('posts:follow_index')
FOLLOW_URL = reverse('posts:profile_follow', kwargs={'username': USERNAME})
UNFOLLOW_URL = reverse('posts:profile_unfollow', kwargs={'username': USERNAME})

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsContextTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username=USERNAME)
        cls.user_2 = User.objects.create_user(username=USERNAME_2)
        cls.group_1 = Group.objects.create(
            title='первая тестовая группа',
            slug=GROUP_SLUG,
            description='Описание первой группы'
        )
        cls.group_2 = Group.objects.create(
            title='вторая тестовая группа',
            slug=GROUP_2_SLUG,
            description='Описание второй группы'
        )
        # Создаем 13 записей в базе:
        # 11 записей (автор_1, группа_1); 2 записи (автор_2, группа_2)
        obj_list = [
            Post(id=i + 1, text=f'{i} тестовый текст',
                 author=cls.user_1, group=cls.group_1) if i < 11 else
            Post(id=i + 1, text=f'{i} тестовый текст',
                 author=cls.user_2, group=cls.group_2) for i in range(13)
        ]
        Post.objects.bulk_create(obj_list, 13)
        for i, post in enumerate(obj_list):
            post.pub_date = datetime.now() + timedelta(hours=i)
        Post.objects.bulk_update(obj_list, ['pub_date'])

        post = Post.objects.get(id=POST_ID)
        post.image = SimpleUploadedFile(
            name='small.gif', content=SMALL_GIF, content_type='image/gif'
        )
        post.save()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user_1)
        self.client_follower = Client()
        self.client_follower.force_login(self.user_2)
        cache.clear()

    def test_paginator(self):
        """Paginator выводит по 10 записей на страницу"""
        # (URL, число записей на странице)
        urls = (
            (INDEX_URL, 10),
            (INDEX_URL + PAGE_2, 3),
            (GROUP_LIST_URL, 10),
            (GROUP_LIST_URL + PAGE_2, 1),
            (PROFILE_URL, 10),
            (PROFILE_URL + PAGE_2, 1),
        )
        for url, pages in urls:
            with self.subTest(url=url):
                self.assertEqual(
                    len(self.client.get(url).context['page_obj'].object_list),
                    pages,
                    'Неправильно работает паджинатор'
                )

    def page_obj_check(self, url, post_list):
        """Функция проверки объекта контекста page_obj"""
        page_obj_list = (
            self.client.get(url).context['page_obj'].paginator.object_list
        )
        for post, post_get in zip(
                post_list.values(), page_obj_list.values()):
            with self.subTest():
                self.assertEqual(post, post_get)

    def model_obj_check(self, url, inst, obj_db):
        """Функция проверки объектов моделей, переданных в context"""
        for key in obj_db:
            with self.subTest(fild=key):
                self.assertEqual(
                    obj_db[key],
                    getattr(self.client.get(url).context.get(inst), key))

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом"""
        self.page_obj_check(
            INDEX_URL, Post.objects.all().order_by('-pub_date')
        )

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом"""
        self.page_obj_check(
            GROUP_LIST_URL, Post.objects.filter(group=1).order_by('-pub_date')
        )
        self.model_obj_check(
            GROUP_LIST_URL,
            'group',
            Group.objects.filter(slug=GROUP_SLUG).values().first()
        )

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        self.page_obj_check(
            PROFILE_URL, Post.objects.filter(author=1).order_by('-pub_date')
        )
        self.model_obj_check(
            PROFILE_URL,
            'author',
            User.objects.filter(username=USERNAME).values().first()
        )

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        self.model_obj_check(
            DETAIL_URL, 'post',
            Post.objects.filter(id=POST_ID).values().first()
        )

    def test_new_post_show_in_pages(self):
        """Созданный пост отображается на главной странице,
        странице своей группы, и профайле автора"""
        new_post = Post.objects.create(
            text='текст нового поста',
            author=PostsContextTest.user_2,
            group=PostsContextTest.group_2,
        )
        # Новый пост отображается на страницах
        url_list = [INDEX_URL, GROUP_2_LIST_URL, PROFILE_2_URL]
        for url in url_list:
            with self.subTest(url=url):
                self.assertIn(
                    new_post,
                    self.client.get(url)
                    .context['page_obj'].paginator.object_list
                )

        # Новый пост не отображается на страницах
        url_list = [GROUP_LIST_URL, PROFILE_URL]
        for url in url_list:
            with self.subTest(url=url):
                self.assertNotIn(
                    new_post,
                    self.client.get(url)
                    .context['page_obj'].paginator.object_list
                )

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        # Страницы, использующие шаблон create_post
        urls = [CREATE_URL, EDIT_URL]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField
        }
        for url in urls:
            with self.subTest(page=url):
                for field, expected in form_fields.items():
                    with self.subTest(field=field):
                        form_field = (
                            self.client.get(url)
                            .context.get('form').fields.get(field)
                        )
                        self.assertIsInstance(form_field, expected)

    def test_index_page_cache(self):
        """Список постов главной страницы хранится в кэше"""
        index_content = self.client.get(INDEX_URL).content
        Post.objects.all().delete()
        self.assertEqual(
            index_content, self.client.get(INDEX_URL).content,
            'страница не сохраняется в кэше'
        )
        cache.clear()
        self.assertNotEqual(
            index_content, self.client.get(INDEX_URL).content,
            'после очистки кэша страница доступна'
        )

    def test_follow_index_page(self):
        """Новая запись автора появляется в ленте подписчиков"""
        self.client_follower.get(FOLLOW_URL)
        new_post = Post.objects.create(
            text='Текст новой записи',
            author=self.user_1
        )
        self.assertIn(
            new_post,
            self.client_follower.get(FOLLOW_INDEX_URL)
            .context['page_obj'].paginator.object_list,
            'новая запись не появляется в ленте подписчика'
        )
        self.assertNotIn(
            new_post,
            self.client.get(FOLLOW_INDEX_URL)
            .context['page_obj'].paginator.object_list,
            'новая запись не должна быть в ленте тех, кто не подписан'
        )


class PostsFollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=USERNAME)
        cls.user = User.objects.create_user(username=USERNAME_2)

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_follow_unfollow(self):
        """Авторизованный пользователь может подписаться на автора"""
        self.client.get(FOLLOW_URL)
        self.assertTrue(
            self.user.follower.filter(author=self.author).exists(),
            'подписка на автора не создана'
        )
        self.client.get(UNFOLLOW_URL)
        self.assertFalse(
            self.user.follower.filter(author=self.author).exists(),
            'подписка на автора не удалена'
        )

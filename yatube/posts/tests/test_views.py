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

INDEX = reverse('posts:index')
GROUP_LIST = reverse('posts:group_list', kwargs={'slug': GROUP_SLUG})
GROUP_2_LIST = reverse('posts:group_list', kwargs={'slug': GROUP_2_SLUG})
PROFILE = reverse('posts:profile', kwargs={'username': USERNAME})
PROFILE_2 = reverse('posts:profile', kwargs={'username': USERNAME_2})
DETAIL = reverse('posts:post_detail', kwargs={'post_id': POST_ID})
CREATE = reverse('posts:post_create')
EDIT = reverse('posts:post_edit', kwargs={'post_id': POST_ID})


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
        # Присваиваем индексы модели Post для возможности обновления
        # записей методом bulk_update
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
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        post = Post.objects.get(id=POST_ID)
        post.image = uploaded
        post.save()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = Client()
        self.client.force_login(PostsContextTest.user_1)
        cache.clear()

    def test_paginator(self):
        """Paginator выводит по 10 записей на страницу"""
        # (URL, число записей на странице)
        urls = [
            (INDEX, 10),
            (INDEX + PAGE_2, 3),
            (GROUP_LIST, 10),
            (GROUP_LIST + PAGE_2, 1),
            (PROFILE, 10),
            (PROFILE + PAGE_2, 1),
        ]
        for url, pages in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    len(response.context['page_obj'].object_list), pages,
                    'Неправильно работает паджинатор'
                )

    def page_obj_check(self, url, post_list):
        """Функция проверки объекта контекста page_obj"""
        response = self.client.get(url)
        page_obj_list = response.context['page_obj'].paginator.object_list
        for post_db, post_get in zip(
                post_list.values(), page_obj_list.values()):
            with self.subTest():
                self.assertEqual(post_db, post_get)

    def model_obj_check(self, url, inst, obj_db):
        """Функция проверки объектов моделей, переданных в context"""
        response = self.client.get(url)
        obj_get = response.context.get(inst)
        for key in obj_db:
            with self.subTest(fild=key):
                self.assertEqual(obj_db[key], getattr(obj_get, key))

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом"""
        post_list = Post.objects.all().order_by('-pub_date')
        self.page_obj_check(INDEX, post_list)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом"""
        post_list = Post.objects.filter(group=1).order_by('-pub_date')
        self.page_obj_check(GROUP_LIST, post_list)
        group_db = Group.objects.filter(slug=GROUP_SLUG).values().first()
        self.model_obj_check(GROUP_LIST, 'group', group_db)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        post_list = Post.objects.filter(author=1).order_by('-pub_date')
        self.page_obj_check(PROFILE, post_list)
        author_db = User.objects.filter(username=USERNAME).values().first()
        self.model_obj_check(PROFILE, 'author', author_db)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        post_db = Post.objects.filter(id=POST_ID).values().first()
        self.model_obj_check(DETAIL, 'post', post_db)

    def test_new_post_show_in_pages(self):
        """Созданный пост отображается на главной странице,
        странице своей группы, и профайле автора"""
        new_post = Post.objects.create(
            text='текст нового поста',
            author=PostsContextTest.user_2,
            group=PostsContextTest.group_2,
        )
        # Новый пост отображается на страницах
        url_list = [INDEX, GROUP_2_LIST, PROFILE_2]
        for url in url_list:
            with self.subTest(url=url):
                response = self.client.get(url)
                obj_list = response.context['page_obj'].paginator.object_list
                self.assertIn(new_post, obj_list)

        # Новый пост не отображается на страницах
        url_list = [GROUP_LIST, PROFILE]
        for url in url_list:
            with self.subTest(url=url):
                response = self.client.get(url)
                obj_list = response.context['page_obj'].paginator.object_list
                self.assertNotIn(new_post, obj_list)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        # Страницы, использующие шаблон create_post
        urls = [CREATE, EDIT]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField
        }
        for url in urls:
            with self.subTest(page=url):
                response = self.client.get(url)
                for field, expected in form_fields.items():
                    with self.subTest(field=field):
                        form_field = (
                            response.context.get('form').fields.get(field)
                        )
                        self.assertIsInstance(form_field, expected)

    def test_index_page_cache(self):
        """Список постов главной страницы хранится в кэше"""
        response = self.client.get(INDEX)
        index_content = response.content

        Post.objects.all().delete()
        response = self.client.get(INDEX)
        self.assertEqual(
            index_content, response.content,
            'страница не сохраняется в кэше'
        )
        cache.clear()
        response = self.client.get(INDEX)
        self.assertNotEqual(
            index_content, response.content,
            'после очистки кэша страница доступна'
        )

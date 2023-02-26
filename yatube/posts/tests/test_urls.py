from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

AUTHOR_USER = 'author_user'
GROUP_SLUG = 'test_slug'

INDEX_URL = reverse('posts:index')
GROUP_LIST_URL = reverse('posts:group_list', kwargs={'slug': GROUP_SLUG})
PROFILE_URL = reverse('posts:profile', kwargs={'username': AUTHOR_USER})
CREATE_URL = reverse('posts:post_create')
PAGE_404 = '/unexisting_page/'
AUTH_URL = '/auth/login/?next=/create/'
DETAIL_NAME = 'posts:post_detail'
EDIT_NAME = 'posts:post_edit'

INDEX_TEMPL = 'posts/index.html'
CROUP_LIST_TEMPL = 'posts/group_list.html'
PROFILE_TEMPL = 'posts/profile.html'
DETAIL_TEMPL = 'posts/post_detail.html'
CREATE_TEMPL = 'posts/create_post.html'
CORE_404_TEMPL = 'core/404.html'


class PostsURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=AUTHOR_USER)
        cls.authorized = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='тестовый текст',
            group=cls.group,
            author=cls.author
        )
        cls.DETAIL_URL = reverse(DETAIL_NAME, kwargs={'post_id': cls.post.id})
        cls.EDIT_URL = reverse(EDIT_NAME, kwargs={'post_id': cls.post.id})

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.authorized)
        self.author_client = Client()
        self.author_client.force_login(self.author)
        cache.clear()

    def test_posts_pages_available_to_all(self):
        """Страница доступна любому пользователю"""
        urls = (INDEX_URL, GROUP_LIST_URL, PROFILE_URL, self.DETAIL_URL)
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(
                    self.guest_client.get(url).status_code, HTTPStatus.OK
                )

    def test_create_page_available_to_authorized(self):
        """Страница /create/ доступна авторизованному пользователю"""
        self.assertEqual(
            self.authorized_client.get(CREATE_URL).status_code, HTTPStatus.OK
        )

    def test_posts_id_edit_page_available_to_author(self):
        """Страница /posts/<post_id>/edit/ доступна автору поста"""
        self.assertEqual(
            self.author_client.get(self.EDIT_URL).status_code, HTTPStatus.OK
        )

    def test_posts_id_edit_page_redirect_authorized_to_posts_id(self):
        """Страница /posts/<post_id>/edit/ перенаправит на страницу поста"""
        self.assertRedirects(
            self.authorized_client.get(self.EDIT_URL, follow=True),
            self.DETAIL_URL
        )

    def test_create_page_redirect_guest_to_login(self):
        """Страница /create/ перенаправит на страницу авторизации"""
        self.assertRedirects(
            self.guest_client.get(CREATE_URL, follow=True), AUTH_URL
        )

    def test_unexisting_url(self):
        """Страница не существует, ошибка 404"""
        self.assertEqual(
            self.guest_client.get(PAGE_404).status_code, HTTPStatus.NOT_FOUND
        )

    def test_posts_pages_uses_correct_template(self):
        """Страница использует правильные шаблоны"""
        url_templates = (
            (INDEX_URL, INDEX_TEMPL),
            (GROUP_LIST_URL, CROUP_LIST_TEMPL),
            (PROFILE_URL, PROFILE_TEMPL),
            (self.DETAIL_URL, DETAIL_TEMPL),
            (self.EDIT_URL, CREATE_TEMPL),
            (CREATE_URL, CREATE_TEMPL),
            (PAGE_404, CORE_404_TEMPL)
        )
        for url, template in url_templates:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)

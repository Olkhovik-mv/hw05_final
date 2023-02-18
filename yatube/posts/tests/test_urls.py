from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

POST_ID = 1
USERNAME = 'author_user'
GROUP_SLUG = 'test_slug'

INDEX = reverse('posts:index')
GROUP_LIST = reverse('posts:group_list', kwargs={'slug': GROUP_SLUG})
PROFILE = reverse('posts:profile', kwargs={'username': USERNAME})
DETAIL = reverse('posts:post_detail', kwargs={'post_id': POST_ID})
CREATE = reverse('posts:post_create')
EDIT = reverse('posts:post_edit', kwargs={'post_id': POST_ID})
PAGE_404 = '/unexisting_page/'


class PostsURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=USERNAME)
        cls.authorized = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            id=POST_ID,
            text='тестовый текст',
            group=cls.group,
            author=cls.author
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTest.authorized)
        self.author_client = Client()
        self.author_client.force_login(PostsURLTest.author)
        cache.clear()

    def test_posts_pages_available_to_all(self):
        """Страница доступна любому пользователю"""
        urls = [INDEX, GROUP_LIST, PROFILE, DETAIL]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_page_available_to_authorized(self):
        """Страница /create/ доступна авторизованному пользователю"""
        response = self.authorized_client.get(CREATE)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_id_edit_page_available_to_author(self):
        """Страница /posts/<post_id>/edit/ доступна автору поста"""
        response = self.author_client.get(EDIT)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_id_edit_page_redirect_authorized_to_posts_id(self):
        """Страница /posts/<post_id>/edit/ перенаправит на страницу поста"""
        response = self.authorized_client.get(EDIT)
        self.assertRedirects(response, DETAIL)

    def test_create_page_redirect_guest_to_login(self):
        """Страница /create/ перенаправит на страницу авторизации"""
        response = self.guest_client.get(CREATE, follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_unexisting_url(self):
        """Страница не существует, ошибка 404"""
        response = self.guest_client.get(PAGE_404)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_posts_pages_uses_correct_template(self):
        """Страница использует правильные шаблоны"""
        url_templates = [
            (INDEX, 'posts/index.html'),
            (GROUP_LIST, 'posts/group_list.html'),
            (PROFILE, 'posts/profile.html'),
            (DETAIL, 'posts/post_detail.html'),
            (EDIT, 'posts/create_post.html'),
            (CREATE, 'posts/create_post.html'),
            (PAGE_404, 'core/404.html')
        ]
        for url, template in url_templates:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)

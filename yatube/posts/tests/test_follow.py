from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, User

FOLLOW_URL = reverse(
    'posts:profile_follow', kwargs={'username': 'author_user'}
)
UNFOLLOW_URL = reverse(
    'posts:profile_unfollow', kwargs={'username': 'author_user'}
)
FOLLOW_INDEX_URL = reverse('posts:follow_index')


class PostsFollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author_user')
        cls.user = User.objects.create_user(username='user')

    def setUp(self):
        self.client = Client()
        self.client.force_login(PostsFollowTest.user)

    def test_follow_unfollow(self):
        """Авторизованный пользователь может подписаться на автора"""
        user = PostsFollowTest.user
        author = PostsFollowTest.author
        self.client.get(FOLLOW_URL)
        self.assertEqual(
            user.follower.filter(author=author).count(), 1,
            'подписка на автора не создана'
        )
        self.client.get(UNFOLLOW_URL)
        self.assertEqual(
            user.follower.filter(author=author).count(), 0,
            'подписка на автора не удалена'
        )

    def test_follow_index_page(self):
        """Новая запись автора появляется в ленте подписчиков"""
        user_follower = User.objects.create_user(username='user_follower')
        self.client_follower = Client()
        self.client_follower.force_login(user_follower)
        self.client_follower.get(FOLLOW_URL)
        new_post = Post.objects.create(
            text='Текст новой записи',
            author=PostsFollowTest.author
        )
        response = self.client_follower.get(FOLLOW_INDEX_URL)
        obj_list = response.context['page_obj'].paginator.object_list
        self.assertIn(
            new_post, obj_list,
            'новая запись не появляется в ленте подписчика'
        )
        response = self.client.get(FOLLOW_INDEX_URL)
        obj_list = response.context['page_obj'].paginator.object_list
        self.assertNotIn(
            new_post, obj_list,
            'новая запись не должна быть в ленте тех, кто не подписан'
        )

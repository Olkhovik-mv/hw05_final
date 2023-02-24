import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

AUTHOR_USER = 'author_user'

CREATE_URL = reverse('posts:post_create')
EDIT_NAME = 'posts:post_edit'
DETAIL_NAME = 'posts:post_detail'
COMMENT_NAME = 'posts:add_comment'

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=AUTHOR_USER)
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.author
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_post_create(self):
        """При отправке валидной формы создается запись в Post"""
        form_data = {
            'text': 'Текст из формы',
            'group': self.group.id,
            'image': SimpleUploadedFile(
                name='small.gif', content=SMALL_GIF, content_type='image/gif'
            )
        }
        posts_count = Post.objects.count()
        self.author_client.post(CREATE_URL, data=form_data)
        self.assertEqual(
            Post.objects.count(), posts_count + 1, 'запись не добавлена'
        )
        post = Post.objects.filter(text=form_data['text']).first()
        self.assertTrue(
            post, 'поле "text" в базе не соответствует отправленному в форме'
        )
        self.assertEqual(
            post.group.id, form_data['group'],
            'поле "group" в базе не равно значению, отправленному в форме'
        )
        self.assertEqual(post.image, 'posts/small.gif')

    def test_post_edit(self):
        """При отправке валидной формы изменяется запись в Post"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Измененный в форме текст',
            'group': self.group.id
        }
        self.author_client.post(
            reverse(EDIT_NAME, kwargs={'post_id': self.post.id}),
            data=form_data
        )
        self.assertEqual(
            Post.objects.count(), posts_count,
            'после редактирования поста изменилось число записей в базе данных'
        )
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(
            post.text, form_data['text'],
            'поле "text" в базе не соответствует тексту, отправленному в форме'
        )
        self.assertEqual(
            post.group.id, form_data['group'],
            'поле "group" в базе не равно значению, отправленному в форме'
        )
        self.assertEqual(
            post.author, self.post.author,
            'после отправки формы изменилось значение author'
        )

    def test_post_add_comments(self):
        """При отправке формы авторизованным пользователем cоздается коммент"""
        comment_url = reverse(COMMENT_NAME, kwargs={'post_id': self.post.id})
        form_comment = {'text': 'Тестовый комментарий'}
        comments_count = self.post.comments.count()
        self.author_client.post(comment_url, data=form_comment)
        self.assertEqual(
            comments_count + 1, self.post.comments.count(),
            'комментарий авторизованного пользователя не добавлен'
        )
        self.guest_client.post(comment_url, data=form_comment)
        self.assertEqual(
            comments_count + 1, self.post.comments.count(),
            'неавторизованный пользователь не может добавлять комментарии'
        )
        # комментарий добавлен на страницу поста
        self.assertIn(
            form_comment['text'], self.guest_client.get(
                reverse(DETAIL_NAME, kwargs={'post_id': self.post.id})
            ).content.decode('utf-8')
        )

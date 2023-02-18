import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
POST_ID = 1


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author_user')
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post_db = Post.objects.create(
            id=POST_ID,
            text='Тестовый текст',
            group=PostsFormTest.group,
            author=PostsFormTest.author
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(PostsFormTest.author)

    def test_post_create(self):
        """При отправке валидной формы создается запись в Post"""
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
        form_data = {
            'text': 'Текст из формы',
            'group': PostsFormTest.group.id,
            'image': uploaded
        }
        posts_count = Post.objects.count()
        self.author_client.post(reverse('posts:post_create'), data=form_data)
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
        post_db = PostsFormTest.post_db
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Измененный в форме текст',
            'group': PostsFormTest.group.id
        }
        self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': POST_ID}),
            data=form_data
        )
        self.assertEqual(
            Post.objects.count(), posts_count,
            'после редактирования поста изменилось число записей в базе данных'
        )
        post_get = Post.objects.get(id=POST_ID)
        self.assertEqual(
            post_get.text, form_data['text'],
            'поле "text" в базе не соответствует тексту, отправленному в форме'
        )
        self.assertEqual(
            post_get.group.id, form_data['group'],
            'поле "group" в базе не равно значению, отправленному в форме'
        )
        self.assertEqual(
            post_get.author, post_db.author,
            'после отправки формы изменилось значение author'
        )

    def test_post_add_comments(self):
        """При отправке формы авторизованным пользователем cоздается коммент"""
        add_comment = reverse('posts:add_comment', kwargs={'post_id': POST_ID})
        post_db = PostsFormTest.post_db
        form_comment = {'text': 'Тестовый комментарий'}
        comments_count = post_db.comments.count()
        self.author_client.post(add_comment, data=form_comment)
        self.assertEqual(
            comments_count + 1, post_db.comments.count(),
            'комментарий авторизованного пользователя не добавлен'
        )
        self.guest_client.post(add_comment, data=form_comment)
        self.assertEqual(
            comments_count + 1, post_db.comments.count(),
            'неавторизованный пользователь не может добавлять комментарии'
        )
        # комментарий добавлен на страницу поста
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': POST_ID})
        )
        comments_list = response.context.get('comments')
        self.assertIsNotNone(
            comments_list, '"comments" не передан в контекст страницы'
        )
        comments = comments_list.filter(text=form_comment['text'])
        self.assertTrue(
            comments.exists(),
            'добавленный комментарий не отображается на странице поста'
        )

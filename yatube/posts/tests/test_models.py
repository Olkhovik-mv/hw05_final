from django.test import TestCase

from posts.models import Group, Post, User


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth = User.objects.create_user(
            username='test_user'
        )
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='тестовый текст длиной более 15 символов',
            group=cls.group,
            author=cls.auth
        )

    def test_post_model_verbose_name(self):
        """Verbose_name модели Post совпадает с ожидаемым"""
        verbose_name = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
            'image': 'Картинка',
        }
        post = PostsModelTest.post
        for field in verbose_name:
            with self.subTest(field=field):
                verbose = post._meta.get_field(field).verbose_name
                self.assertEqual(verbose, verbose_name[field])

    def test_post_model_help_text(self):
        """Help_text модели Post совпадет с ожидаемым"""
        help_text = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        post = PostsModelTest.post
        for field in help_text:
            with self.subTest(field=field):
                help = post._meta.get_field(field).help_text
                self.assertEqual(help, help_text[field])

    def test_post_model_str_method(self):
        """Метод __str__ модели Post
        возвращает первые пятнадцать символов поля text."""
        post = PostsModelTest.post
        self.assertEqual(post.text[:15], str(post))

    def test_group_model_str_method(self):
        """Метод __str__ модели Group возвращает значение поля title."""
        group = PostsModelTest.group
        self.assertEqual(group.title, str(group))

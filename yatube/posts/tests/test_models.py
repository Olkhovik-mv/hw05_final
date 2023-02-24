from django.test import TestCase

from posts.models import Comment, Follow, Group, Post, User


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth = User.objects.create_user(username='user')
        cls.post = Post.objects.create(
            text='тестовый текст длиной более 15 символов',
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
        for field in verbose_name:
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).verbose_name,
                    verbose_name[field]
                )

    def test_post_model_help_text(self):
        """Help_text модели Post совпадет с ожидаемым"""
        help_text = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field in help_text:
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).help_text,
                    help_text[field]
                )

    def test_group_model_verbose_name(self):
        """Verbose_name модели Group совпадает с ожидаемым"""
        verbose_name = {
            'title': 'Название группы',
            'slug': 'URL',
            'description': 'Описание',
        }
        for field in verbose_name:
            with self.subTest(field=field):
                self.assertEqual(
                    Group._meta.get_field(field).verbose_name,
                    verbose_name[field]
                )

    def test_comment_model_verbose_name(self):
        """Verbose_name модели Comment совпадает с ожидаемым"""
        verbose_name = {
            'post': 'Комментируемый пост',
            'author': 'Автор комментария',
            'created': 'Дата публикации',
            'text': 'Текст комментария',
        }
        for field in verbose_name:
            with self.subTest(field=field):
                self.assertEqual(
                    Comment._meta.get_field(field).verbose_name,
                    verbose_name[field]
                )

    def test_follow_model_verbose_name(self):
        """Verbose_name модели Follow совпадает с ожидаемым"""
        verbose_name = {
            'user': 'Подписчик',
            'author': 'Автор',
        }
        for field in verbose_name:
            with self.subTest(field=field):
                self.assertEqual(
                    Follow._meta.get_field(field).verbose_name,
                    verbose_name[field]
                )

    def test_post_model_str_method(self):
        """Метод __str__ модели Post
        возвращает первые пятнадцать символов поля text."""
        self.assertEqual(self.post.text[:15], str(self.post))

    def test_group_model_str_method(self):
        """Метод __str__ модели Group возвращает значение поля title."""
        group = Group.objects.create(
            title='тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание'
        )
        self.assertEqual(group.title, str(group))

    def test_comment_model_str_method(self):
        """Метод __str__ модели Comment
        возвращает первые пятнадцать символов поля text"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.auth,
            text='текст комментария длиной более 15 символов'
        )
        self.assertEqual(comment.text[:15], str(comment))

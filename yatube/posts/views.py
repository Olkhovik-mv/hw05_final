from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from core.utils import get_page_obj

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User

POSTS_ON_PAGE = 10


# Главная страница
@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.select_related('group', 'author').all()
    page_obj = get_page_obj(post_list, POSTS_ON_PAGE, request)
    context = {'page_obj': page_obj}
    template = 'posts/index.html'
    return render(request, template, context)


# Посты, отфильтрованные по группам
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author').all()
    page_obj = get_page_obj(post_list, POSTS_ON_PAGE, request)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    template = 'posts/group_list.html'
    return render(request, template, context)


# Персональная страница пользователя
def profile(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    following = False
    if isinstance(user, User):
        if author.following.filter(user=user):
            following = True
    author_posts = author.posts.select_related('group').all()
    page_obj = get_page_obj(author_posts, POSTS_ON_PAGE, request)
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    template = 'posts/profile.html'
    return render(request, template, context)


# Страница поста
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.select_related('author').all()
    form = CommentForm()
    context = {'post': post, 'comments': comments, 'form': form}
    template = 'posts/post_detail.html'
    return render(request, template, context)


# Новый пост
@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if not form.is_valid():
        template = 'posts/create_post.html'
        context = {'form': form}
        return render(request, template, context)
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect(f'/profile/{post.author.username}/')


# Редактирование поста
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect(f'/posts/{post_id}/')
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if not form.is_valid():
        template = 'posts/create_post.html'
        context = {'is_edit': True, 'post_id': post_id, 'form': form}
        return render(request, template, context)
    form.save()
    return redirect(f'/posts/{post_id}/')


# Обработка комментария
@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


# Посты избранных авторов
@login_required
def follow_index(request):
    user = request.user
    follow_qs = user.follower.all()
    author_list = [user.author for user in follow_qs]
    post_list = (
        Post.objects.select_related('group', 'author')
        .filter(author__in=author_list)
    )
    page_obj = get_page_obj(post_list, POSTS_ON_PAGE, request)
    context = {'page_obj': page_obj, 'follow': True}
    return render(request, 'posts/index.html', context)


# Подписаться
@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    if user != author:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', username=username)


# Отписаться
@login_required
def profile_unfollow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    user.follower.filter(author=author).delete()
    return redirect('posts:index')

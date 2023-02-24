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
    return render(request, 'posts/index.html', {
        'page_obj': get_page_obj(
            Post.objects.select_related('group', 'author').all(),
            POSTS_ON_PAGE, request
        ),
        'index': True
    }
    )


# Посты, отфильтрованные по группам
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': get_page_obj(
            group.posts.select_related('author').all(), POSTS_ON_PAGE, request
        )
    }
    )


# Персональная страница пользователя
def profile(request, username):
    author = get_object_or_404(User, username=username)
    return render(request, 'posts/profile.html', {
        'author': author,
        'page_obj': get_page_obj(
            author.posts.select_related('group').all(), POSTS_ON_PAGE, request
        ),
        'following': request.user.is_authenticated
        and request.user.username != username
        and author.following.filter(user=request.user)
    }
    )


# Страница поста
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'form': CommentForm()
    }
    )


# Новый пост
@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=request.user.username)


# Редактирование поста
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'is_edit': True, 'post_id': post_id, 'form': form
        }
        )
    form.save()
    return redirect('posts:post_detail', post_id=post_id)


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
    return render(request, 'posts/index.html', {
        'page_obj': get_page_obj(
            Post.objects.select_related('group', 'author')
            .filter(author__following__user=request.user),
            POSTS_ON_PAGE, request
        ),
        'follow': True
    }
    )


# Подписаться
@login_required
def profile_follow(request, username):
    if request.user.username != username:
        author = get_object_or_404(User, username=username)
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


# Отписаться
@login_required
def profile_unfollow(request, username):
    get_object_or_404(
        Follow, user=request.user, author__username=username
    ).delete()
    return redirect('posts:index')

from .models import Post, Group, User
from django.contrib.auth.decorators import login_required
from .forms import PostForm
from .utils import paginator
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)


def index(request):
    post_list = Post.objects.all()
    page_obj = paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = paginator(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page_obj = paginator(request, post_list)
    context = {
        'author': author,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    context = {
        'post': post,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            post_object = form.save(commit=False)
            post_object.author = request.user
            post_object.save()
            return redirect('posts:profile', request.user.username)
        return render(request, 'posts/post_create.html', {'form': form})
    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)

    form = PostForm(request.POST or None, instance=post)
    if request.method == 'POST':
        if form.is_valid():
            post_object = form.save(commit=False)
            post_object.author = request.user
            post_object.save()
            return redirect('posts:post_detail', post.id)

        return render(
            request,
            'posts/post_create.html',
            {'is_edit': True, 'form': form}
        )

    return render(
        request,
        'posts/post_create.html',
        {'is_edit': True, 'form': form}
    )

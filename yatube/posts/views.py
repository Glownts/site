from .models import Follow, Post, Group, Comment, User
from .forms import PostForm, CommentForm
from .utils import pagination


from django.urls import reverse
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    View
)


class IndexView(ListView):
    '''Класс-представление главной страницы.'''
    paginate_by = settings.POSTS_PER_PAGE_LIMIT
    model = Post
    template_name = 'posts/index.html'


class GroupPostsView(DetailView):
    '''Класс-представление страницы группы.'''
    template_name = 'posts/group_list.html'
    model = Group
    slug_url_kwarg = 'slug'
    paginate_by = settings.POSTS_PER_PAGE_LIMIT

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        posts = group.posts.all()
        page_obj = pagination(self, posts)
        context['page_obj'] = page_obj
        context['group'] = group
        return context


class ProfileView(DetailView):
    '''Класс-представление страницы пользователя.'''
    template_name = 'posts/profile.html'
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    paginate_by = settings.POSTS_PER_PAGE_LIMIT

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        author = self.get_object()
        user = self.request.user
        posts = author.posts.all()
        page_obj = pagination(self, posts)
        following = False
        if user.is_authenticated:
            following = Follow.objects.filter(
                user=user,
                author=author
            ).exists()
        context['author'] = author
        context['page_obj'] = page_obj
        context['following'] = following
        return context


class PostDetailView(DetailView):
    '''Класс-представление страницы записи.'''
    model = Post
    template_name = 'posts/post_detail.html'
    pk_url_kwarg = 'post_id'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = CommentForm()
        comments = Comment.objects.filter(post__id=self.kwargs['post_id'])
        context['form'] = form
        context['comments'] = comments
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    '''Класс-представление создания записи.'''
    template_name = 'posts/post_create.html'
    model = Post
    form_class = PostForm

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs())

    def get_form_kwargs(self):
        kwargs = {
            'initial': self.get_initial(),
            'prefix': self.get_prefix(),
        }

        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    def form_valid(self, form):
        post_object = form.save(commit=False)
        post_object.author = User.objects.get(username=self.request.user)
        post_object.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'posts:profile',
            kwargs={'username': self.request.user.username}
        )


class PostEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    '''Класс-представление редактирования записи.'''
    template_name = 'posts/post_create.html'
    model = Post
    form_class = PostForm
    pk_url_kwarg = 'post_id'
    extra_context = {'is_edit': True}

    def test_func(self):
        author = self.get_object().author
        if self.request.user == author:
            return True
        return False

    def handle_no_permission(self):
        if self.raise_exception or self.request.user.is_authenticated:
            return redirect('posts:post_detail', self.get_object().id)
        return redirect_to_login(
            self.request.get_full_path(),
            self.get_login_url(),
            self.get_redirect_field_name()
        )

    def get_success_url(self):
        return reverse('posts:post_detail', kwargs={'post_id': self.object.id})


class AddCommentView(LoginRequiredMixin, CreateView):
    '''Класс-представление создания комментария.'''
    template_name = 'posts/post_detail.html'
    form_class = CommentForm
    model = Comment
    pk_url_kwarg = 'post_id'

    def get(self, *args, **kwargs):
        return redirect('posts:post_detail', post_id=self.kwargs['post_id'])

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.author = self.request.user
        comment.post = Post.objects.get(id=self.kwargs['post_id'])
        comment.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'posts:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class FollowIndexView(LoginRequiredMixin, ListView):
    '''Класс-представление страницы подписок.'''
    paginate_by = settings.POSTS_PER_PAGE_LIMIT
    model = Post
    template_name = 'posts/follow.html'

    def get_queryset(self):
        return Post.objects.filter(author__following__user=self.request.user)


class ProfileFollow(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        author = User.objects.get(username=self.kwargs['username'])
        user = request.user
        if user != author:
            Follow.objects.get_or_create(
                user=user,
                author=author
            )
        return redirect('posts:profile', username=self.kwargs['username'])


class ProfileUnfollow(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        author = User.objects.get(username=self.kwargs['username'])
        user = request.user
        Follow.objects.filter(
            user=user,
            author=author
        ).delete()
        return redirect('posts:profile', username=self.kwargs['username'])

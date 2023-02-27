from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    '''Форма для создания/редактирования новой записи.'''
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст записи',
            'group': 'Группа',
            'image': 'Изображение',
        }
        help_texts = {
            'text': 'Текст новой записи',
            'group': 'Группа, к которой будет относиться запись',
            'image': 'Изображение',
        }


class CommentForm(forms.ModelForm):
    '''Форма отправки комментариев.'''
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст комментария'
        }
        help_texts = {
            'text': 'Напишите комментарий'
        }

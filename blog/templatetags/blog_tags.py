import markdown
from django import template
from django.db.models import Count
from django.utils.safestring import mark_safe

from ..models import Post

# нужна для того, чтобы быть допустимой библиотекой тегов
# используется для регистрации шаблонных тегов и фильтров приложения
register = template.Library()


# Создание шаблонного тега вывода колличества постов
# декоратор создает ее под именем
@register.simple_tag
def total_posts():
    return Post.published.count()


# Создание шаблонного тега включения
@register.inclusion_tag('blog/post/latest_posts.html')
def show_latest_posts(count=5):
    latest_posts = Post.published.order_by('-publish')[:count]
    return {'latest_posts': latest_posts}


# Создание шаблонного тега, возвращающего набор запросов
# Отображение постов с наибольшим количеством комментариев
@register.simple_tag
def get_most_commented_posts(count=5):
    return Post.published.annotate(total_comments=Count('comments')).order_by('-total_comments')[:count]


# Создание прикладного фильтра для использования markdown
@register.filter(name='markdown')
def markdown_format(text):
    return mark_safe(markdown.markdown(text))

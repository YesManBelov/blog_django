from django.contrib.postgres.search import TrigramSimilarity, SearchVector, SearchQuery, SearchRank
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.shortcuts import render, get_object_or_404
from django.db.models import Count

from taggit.models import Tag

from .models import Post, Comment
from .forms import EmailPostForm, CommentForm, SearchForm


class PostListView(ListView):
    """
    Представление списка постов на основе класса
    """
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_list(request, tag_slug=None):
    """
    Представления списка постов на основе функции
    """
    posts_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        posts_list = posts_list.filter(tags__in=[tag])  # поиск по конкретному тэгу

    # Постраничная разбивка
    paginator = Paginator(posts_list, 3)
    page_number = request.GET.get('page', 1)

    try:
        posts = paginator.page(page_number)
    except EmptyPage:
        # page nuber wrong
        # выдадим последнюю
        posts = paginator.page(paginator.num_pages)
    except PageNotAnInteger:
        # Если не число передано в аргумент
        # выдадим первую
        posts = paginator.page(1)
    return render(request,
                  'blog/post/list.html',
                  {'posts': posts,
                   'tag': tag})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day,
                             status=Post.Status.PUBLISHED)
    # Список активных комментариев е этому посту
    comments = post.comments.filter(active=True)

    # форма для комментирования пользователями
    form = CommentForm()

    # Список похожих постов
    # получение id всех тэгов от этого поста
    post_tags_ids = post.tags.values_list('id', flat=True)  # flat=true делает [1,2,3] а не [(1,), (2,), (3,)]
    # получение всех постов
    similar_posts = Post.published.filter(tags__in=post_tags_ids) \
        .exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')) \
                        .order_by('-same_tags', '-publish')[:4]

    return render(request,
                  'blog/post/detail.html',
                  {'post': post,
                   'comments': comments,
                   'form': form,
                   'similar_posts': similar_posts})


def post_share(request, post_id):
    # Извлекаем пост по идентификатору id
    post = get_object_or_404(Post,
                             id=post_id,
                             status=Post.Status.PUBLISHED)

    sent = False

    if request.method == 'POST':
        # Форма была передана в обработку
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Поля успешно прошли валидацию
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} тебе рекомендует почитать" \
                      f"{post.title}"
            message = f"Читать {post.title} по адресу: {post_url}\n\n" \
                      f"{cd['name']} комментирует: {cd['comments']}"
            send_mail(subject, message, 'nikolai@ozereshno.online',
                      [cd['to']])
            sent = True

    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post,
                                                    'form': form,
                                                    'sent': sent})


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id,
                             status=Post.Status.PUBLISHED)
    comment = None
    # Комментарий был отправлен
    form = CommentForm(data=request.POST)
    if form.is_valid():
        # создать объект класса, но не сохранять его в базу
        comment = form.save(commit=False)
        # назначить пост комментария
        comment.post = post
        # теперь сохранить
        comment.save()

    return render(request, 'blog/post/comment.html',
                  {'post': post,
                   'form': form,
                   'comment': comment})


def post_search(request):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']

            # поиск по веса, рангу конфигу стоп слов
            # search_vector = SearchVector('title', weight='A', config='russian') + \
            #     SearchVector('body', weight='B', config='russian')
            # search_query = SearchQuery(query, config='russian')
            # results = Post.published.annotate(
            #     search=search_vector,
            #     rank=SearchRank(search_vector, search_query)
            # ).filter(rank__gte=0.3).order_by('-rank')

            # Поиск по триграмному сходству
            # он может искать опечатки
            # для базы данных нужно установить расширение CREATE EXTENSION pg_trgm;
            results = Post.published.annotate(
                similarity=TrigramSimilarity('title', query),
            ).filter(similarity__gt=0.1).order_by('-similarity')

    return render(request,
                  'blog/post/search.html',
                  {'form': form,
                   'query': query,
                   'results': results})

git filter-branch --env-filter '
OLD_EMAIL="afoton777@gmail.com"
CORRECT_NAME="Nikolaus"
CORRECT_EMAIL="nikolai@nmeev.ru"
if [ "$GIT_COMMITTER_EMAIL" = "$OLD_EMAIL" ]
then
    export GIT_COMMITTER_NAME="$CORRECT_NAME"
    export GIT_COMMITTER_EMAIL="$CORRECT_EMAIL"
fi
if [ "$GIT_AUTHOR_EMAIL" = "$OLD_EMAIL" ]
then
    export GIT_AUTHOR_NAME="$CORRECT_NAME"
    export GIT_AUTHOR_EMAIL="$CORRECT_EMAIL"
fi
' --tag-name-filter cat -- --branches --tags

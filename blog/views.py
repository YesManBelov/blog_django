from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from .models import Post
from .forms import EmailPostForm


class PostListView(ListView):
    """
    Представление списка постов на основе класса
    """
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_list(request):
    """
    Представления списка постов на основе функции
    """
    posts_list = Post.published.all()
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
                  {'posts': posts})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day,
                             status=Post.Status.PUBLISHED)
    return render(request,
                  'blog/post/detail.html',
                  {'post': post})


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
            print(cd['to'])
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} тебе рекомендует почитать"\
                      f"{post.title}"
            message = f"Читать {post.title} по адресу: {post_url}\n\n"\
                      f"{cd['name']} комментирует: {cd['comments']}"
            send_mail(subject, message, 'nikolai@ozereshno.online',
                      [cd['to']])
            sent = True

    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post,
                                                    'form': form,
                                                    'sent': sent})

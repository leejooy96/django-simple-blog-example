from django.http import HttpResponse
from django.utils import timezone
from blog.models import Post, Comment

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .forms import PostForm, CommentForm, RegisterForm

import json


def main(request):
    return render(request, 'main.html', {})


def register(request):
    form = RegisterForm()

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main')
        else:
            form = RegisterForm(form.errors)

    return render(request, 'registration/register.html', {'form': form})


def about(request):
    return render(request, 'about.html', {})


def post_list(request):
    posts_list = Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')

    paginator = Paginator(posts_list, 10)

    page = request.GET.get('page')

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    return render(request, 'post_list.html', {'posts': posts_list})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm()

    # post comment
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.save()
            return redirect('post_detail', pk=post.pk)
        else:
            form = CommentForm()

    user_id = request.user
    if not user_id.is_anonymous:
        form.initial = {'author': user_id}
    return render(request, 'post_detail.html', {'post': post, 'form': form})


@login_required
def post_add(request):
    if request.method == "POST":
        form = PostForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()

    return render(request, 'post_edit.html', {'form': form})


@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if request.user != post.author and not request.user.is_superuser:
        form = CommentForm()
        return render(request, 'post_detail.html', {'post': post, 'form': form})

    if request.method == "POST":
        form = PostForm(request.POST, instance=post)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)

    return render(request, 'post_edit.html', {'form': form})


@login_required
def post_delete(request, pk):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=pk)
        if post.author == request.user or request.user.is_superuser:
            post.delete()

        return redirect('post_list')


def comment_like(request):
    if request.method == 'POST':
        json_data = json.loads(request.body)
        comment_id = json_data['pk']
        comment = get_object_or_404(Comment, pk=comment_id)

        if not request.user.is_authenticated:
            context = {'likes': comment.like.count(), 'success': 'authRequired'}
        else:
            user_id = request.user.id

            if comment.like.filter(id=user_id).exists():
                comment.like.remove(user_id)
                message = 'removed'
            else:
                comment.like.add(user_id)
                message = 'added'

            context = {'likes': comment.like.count(), 'success': message}

        return HttpResponse(json.dumps(context), content_type='application/json')


def comment_delete(request):
    if request.method == 'POST':
        json_data = json.loads(request.body)
        comment_id = json_data['pk']
        comment = get_object_or_404(Comment, pk=comment_id)

        if not request.user.is_authenticated:
            context = {'success': 'authRequired'}
        else:
            if comment.author == request.user.username or request.user.is_superuser:
                comment.delete()
                message = 'removed'
            else:
                message = 'notOwned'

            context = {'success': message}

        return HttpResponse(json.dumps(context), content_type='application/json')

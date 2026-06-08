from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ForumTopic, ForumPost

def forum_index(request):
    topics = ForumTopic.objects.all().order_by('-updated_at')
    return render(request, 'community/forum_index.html', {'topics': topics, 'title': 'Форум'})

def topic_detail(request, topic_id):
    topic = get_object_or_404(ForumTopic, id=topic_id)
    topic.views += 1
    topic.save()
    posts = topic.posts.all()
    return render(request, 'community/topic_detail.html', {'topic': topic, 'posts': posts})

@login_required
def create_topic(request):
    if request.method == 'POST':
        topic = ForumTopic.objects.create(
            title=request.POST.get('title'),
            category=request.POST.get('category'),
            author=request.user
        )
        ForumPost.objects.create(
            topic=topic,
            author=request.user,
            content=request.POST.get('content')
        )
        return redirect('community:topic_detail', topic_id=topic.id)
    return render(request, 'community/create_topic.html', {'title': 'Создать тему'})

@login_required
def add_reply(request, topic_id):
    if request.method == 'POST':
        topic = get_object_or_404(ForumTopic, id=topic_id)
        ForumPost.objects.create(
            topic=topic,
            author=request.user,
            content=request.POST.get('content')
        )
        topic.updated_at = timezone.now()
        topic.save()
        return redirect('community:topic_detail', topic_id=topic_id)
    return redirect('community:forum_index')

@login_required
def like_post(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
    return redirect('community:topic_detail', topic_id=post.topic.id)

def user_gallery(request):
    return render(request, 'community/user_gallery.html', {'title': 'Фотогалерея'})

def upload_photo(request):
    if request.method == 'POST':
        # Логика загрузки фото
        pass
    return render(request, 'community/upload_photo.html', {'title': 'Загрузить фото'})

def qa_index(request):
    return render(request, 'community/qa_index.html', {'title': 'Вопросы и ответы'})

def ask_question(request):
    if request.method == 'POST':
        # Логика создания вопроса
        pass
    return render(request, 'community/ask_question.html', {'title': 'Задать вопрос'})
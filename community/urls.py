from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    path('', views.forum_index, name='forum_index'),
    path('topic/<int:topic_id>/', views.topic_detail, name='topic_detail'),
    path('topic/create/', views.create_topic, name='create_topic'),
    path('gallery/', views.user_gallery, name='user_gallery'),
    path('qa/', views.qa_index, name='qa_index'),
]
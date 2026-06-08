# pages/models.py
from django.db import models
from django.urls import reverse


class Article(models.Model):
    """Статья в блоге"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True)
    image = models.ImageField(upload_to='blog/', null=True, blank=True)
    author = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    is_published = models.BooleanField(default=True)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('pages:blog_detail', args=[self.slug])
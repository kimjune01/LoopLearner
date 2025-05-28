from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Email management
    path('emails/', views.list_emails, name='list_emails'),
    path('emails/generate/', views.generate_fake_email, name='generate_fake_email'),
    path('emails/<int:email_id>/drafts/', views.get_email_drafts, name='get_email_drafts'),
    path('emails/<int:email_id>/drafts/generate/', views.generate_drafts, name='generate_drafts'),
    path('emails/<int:email_id>/feedback/', views.submit_feedback, name='submit_feedback'),
    
    # Optimization
    path('optimization/status/', views.optimization_status, name='optimization_status'),
]
"""
URL configuration for sidecrewproject project.
"""
from . import views
from django.urls import path

urlpatterns = [
    path('', views.index, name='index'),

    # Client Paths
    path('client_register', views.client_register, name='client_register'),
    path('client_login', views.client_login, name='client_login'),
    path('client_home', views.client_home, name='client_home'),
    path('client_profile', views.client_profile, name='client_profile'),
    path('delete_client_profile', views.delete_client_profile, name='delete_client_profile'),
    path('create_job', views.create_job, name='create_job'),
    path('job/<int:job_id>/delete/', views.delete_job, name='delete_job'),
    path('client/job/pay/<int:job_id>/', views.client_pay_for_job, name='client_pay_for_job'),
    path('rate/agent/<int:job_id>/', views.client_rate_agent, name='client_rate_agent'),
    path('api/get-agents-near/', views.get_agents_near, name='get_agents_near'),

    # Worker Paths
    path('worker_register', views.worker_register, name='worker_register'),
    path('worker_login', views.worker_login, name='worker_login'),
    path('worker_home', views.worker_home, name='worker_home'),
    path('worker_profile', views.worker_profile, name='worker_profile'),
    path('delete_worker_profile', views.delete_worker_profile, name='delete_worker_profile'),
    path('worker/apply/<int:posting_id>/', views.apply_for_job, name='apply_for_job'),

    # --- NEW WORKER PROOF URL ---
    path('application/<int:application_id>/upload-proof/',
         views.worker_upload_proof,
         name='worker_upload_proof'), # <-- ADDED

    # Agent Paths
    path('agent_register', views.agent_register, name='agent_register'),
    path('agent_login', views.agent_login, name='agent_login'),
    path('agent_home', views.agent_home, name='agent_home'),
    path('agent_profile', views.agent_profile, name='agent_profile'),
    path('delete_agent_profile', views.delete_agent_profile, name='delete_agent_profile'),
    path('agent/job/<int:job_id>/accept/', views.accept_job, name='accept_job'),
    path('agent/create_posting/<int:job_id>/', views.create_job_posting, name='create_job_posting'),
    path('agent/application/accept/<int:application_id>/', views.accept_application, name='accept_application'),
    path('agent/application/reject/<int:application_id>/', views.reject_application, name='reject_application'),
    path('agent/application/mark-paid/<int:application_id>/', views.agent_mark_worker_paid, name='agent_mark_worker_paid'),
    path('rate/worker/<int:application_id>/', views.agent_rate_worker, name='agent_rate_worker'),
    path('agent/invite/accept/<int:job_id>/', views.accept_direct_invite, name='accept_direct_invite'),
    path('agent/invite/reject/<int:job_id>/', views.reject_direct_invite, name='reject_direct_invite'),

    # --- NEW AGENT PROOF URLS ---
    path('agent/review-proofs/',
         views.agent_review_dashboard,
         name='agent_review_dashboard'), # <-- ADDED
    path('agent/proof/<int:proof_id>/approve/',
         views.agent_approve_proof,
         name='agent_approve_proof'), # <-- ADDED
    path('agent/proof/<int:proof_id>/reject/',
         views.agent_reject_proof,
         name='agent_reject_proof'), # <-- ADDED

    # Admin Paths
    path('admin_login', views.admin_login, name='admin_login'),
    path('admin_home', views.admin_home, name='admin_home'),
    path('admin_manage_jobs', views.admin_manage_jobs, name='admin_manage_jobs'),
    path('admin_delete_job/<int:job_id>/', views.admin_delete_job, name='admin_delete_job'),
    path('admin_job_detail/<int:job_id>/', views.admin_job_detail, name='admin_job_detail'),

    # Logout
    path('user_logout', views.user_logout, name='user_logout'),

    # --- NEW ADMIN MANAGEMENT URLS ---
    path('manage_clients', views.manage_clients, name='manage_clients'),
    path('approve_client/<int:pk>/', views.approve_client, name='approve_client'),
    path('reject_client/<int:pk>/', views.reject_client, name='reject_client'),
    path('delete_client/<int:pk>/', views.delete_client, name='delete_client'),

    path('manage_workers', views.manage_workers, name='manage_workers'),
    path('approve_worker/<int:pk>/', views.approve_worker, name='approve_worker'),
    path('reject_worker/<int:pk>/', views.reject_worker, name='reject_worker'),
    path('delete_worker/<int:pk>/', views.delete_worker, name='delete_worker'),

    path('manage_agents', views.manage_agents, name='manage_agents'),
    path('approve_agent/<int:pk>/', views.approve_agent, name='approve_agent'),
    path('reject_agent/<int:pk>/', views.reject_agent, name='reject_agent'),
    path('delete_agent/<int:pk>/', views.delete_agent, name='delete_agent'),
]
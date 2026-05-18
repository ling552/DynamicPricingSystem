from django.urls import path

from . import views

urlpatterns = [
    path("intro/", views.intro_page, name="intro_page"),
    path("", views.dashboard, name="dashboard"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("products/", views.product_list, name="product_list"),
    path("products/new/", views.product_create, name="product_create"),
    path("products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("sales/", views.sales_list, name="sales_list"),
    path("sales/new/", views.sales_create, name="sales_create"),
    path("sales/<int:pk>/edit/", views.sales_edit, name="sales_edit"),
    path("sales/<int:pk>/delete/", views.sales_delete, name="sales_delete"),
    path("simulate/", views.simulate, name="simulate"),
    path("results/<int:pk>/", views.simulation_detail, name="simulation_detail"),
    path("analysis/", views.analysis_dashboard, name="analysis_dashboard"),
]

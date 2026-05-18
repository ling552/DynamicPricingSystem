from django.contrib import admin

from .models import Product, SalesRecord, SimulationResult


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "price", "cost", "price_sensitivity", "created_by")
    search_fields = ("name", "category", "created_by__username")
    list_filter = ("category",)


@admin.register(SalesRecord)
class SalesRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "sale_date", "price", "quantity")
    list_filter = ("sale_date", "product")


@admin.register(SimulationResult)
class SimulationResultAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "strategy",
        "base_price",
        "new_price",
        "base_sales",
        "predicted_sales",
        "base_profit",
        "predicted_profit",
        "created_by",
        "created_at",
    )
    list_filter = ("created_at", "product")
    search_fields = ("strategy", "product__name", "created_by__username")

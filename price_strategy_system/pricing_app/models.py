from django.conf import settings
from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=255)
    cost = models.FloatField()
    price = models.FloatField()
    category = models.CharField(max_length=255, blank=True)
    price_sensitivity = models.FloatField(default=0.5)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class SalesRecord(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales")
    sale_date = models.DateField()
    price = models.FloatField()
    quantity = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-sale_date", "-id"]

    def __str__(self):
        return f"{self.product.name} {self.sale_date}"


class SimulationResult(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="simulations"
    )
    strategy = models.CharField(max_length=255)
    base_price = models.FloatField()
    new_price = models.FloatField()
    price_change_rate = models.FloatField()
    base_sales = models.IntegerField()
    predicted_sales = models.IntegerField()
    base_profit = models.FloatField()
    predicted_profit = models.FloatField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="simulations"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.product.name} {self.strategy}"

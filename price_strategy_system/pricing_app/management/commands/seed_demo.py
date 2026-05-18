from __future__ import annotations

import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from pricing_app.models import Product, SalesRecord, SimulationResult
from pricing_app.services import simulate_price_change


class Command(BaseCommand):
    help = "Seed demo data (demo user, products, sales records, simulation results)."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="demo")
        parser.add_argument("--password", default="demo12345")
        parser.add_argument("--products", type=int, default=3)
        parser.add_argument("--days", type=int, default=14)
        parser.add_argument("--force", action="store_true", help="Recreate demo data")

    @transaction.atomic
    def handle(self, *args, **options):
        username: str = options["username"]
        password: str = options["password"]
        products_n: int = options["products"]
        days: int = options["days"]
        force: bool = bool(options["force"])

        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.save()
        else:
            if force:
                SimulationResult.objects.filter(created_by=user).delete()
                SalesRecord.objects.filter(product__created_by=user).delete()
                Product.objects.filter(created_by=user).delete()
            if not user.check_password(password):
                user.set_password(password)
                user.save()

        if Product.objects.filter(created_by=user).exists() and not force:
            self.stdout.write(self.style.WARNING("Demo data already exists. Use --force to recreate."))
            self.stdout.write(self.style.SUCCESS(f"Login: {username} / {password}"))
            return

        categories = ["饮料", "零食", "日用品", "电子"]
        product_names = [
            "奶茶",
            "苏打水",
            "薯片",
            "巧克力",
            "洗衣液",
            "蓝牙耳机",
            "充电线",
        ]
        random.shuffle(product_names)

        products: list[Product] = []
        for i in range(products_n):
            name = product_names[i % len(product_names)]
            cost = round(random.uniform(3, 40), 2)
            price = round(cost * random.uniform(1.2, 1.8), 2)
            p = Product.objects.create(
                name=f"{name}#{i+1}",
                cost=cost,
                price=price,
                category=random.choice(categories),
                price_sensitivity=round(random.uniform(0.2, 1.2), 2),
                created_by=user,
            )
            products.append(p)

        today = timezone.localdate()
        for p in products:
            for d in range(days):
                sale_date = today - timedelta(days=(days - 1 - d))
                quantity = int(max(0, round(random.gauss(30, 8))))
                if quantity == 0:
                    quantity = random.randint(5, 15)

                price = round(float(p.price) * random.uniform(0.9, 1.1), 2)

                SalesRecord.objects.create(
                    product=p,
                    sale_date=sale_date,
                    price=price,
                    quantity=quantity,
                )

        # simulations
        for p in products:
            base_sales = sum(
                SalesRecord.objects.filter(product=p).values_list("quantity", flat=True)
            )
            if base_sales <= 0:
                base_sales = 50

            for pct in (-0.1, 0.05, 0.12):
                metrics = simulate_price_change(
                    product=p,
                    price_change_rate=float(pct),
                    base_sales=int(base_sales),
                )
                strategy = f"Demo 调整 {round(metrics.price_change_rate * 100, 2)}%"
                SimulationResult.objects.create(
                    product=p,
                    strategy=strategy,
                    base_price=float(p.price),
                    new_price=float(metrics.new_price),
                    price_change_rate=float(metrics.price_change_rate),
                    base_sales=int(metrics.base_sales),
                    predicted_sales=int(metrics.predicted_sales),
                    base_profit=float(metrics.base_profit),
                    predicted_profit=float(metrics.predicted_profit),
                    created_by=user,
                )

        self.stdout.write(self.style.SUCCESS("Seed demo data done."))
        self.stdout.write(self.style.SUCCESS(f"Login: {username} / {password}"))
        self.stdout.write(self.style.SUCCESS("Admin: /admin/ (same credentials)"))

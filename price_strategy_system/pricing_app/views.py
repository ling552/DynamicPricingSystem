from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import (
    AdminPasswordResetForm,
    AdminUserForm,
    AnalysisFilterForm,
    LoginForm,
    ProductForm,
    ProfileForm,
    ProfilePasswordForm,
    RegisterForm,
    SalesRecordForm,
    SimulationForm,
)
from .models import Product, SalesRecord, SimulationResult
from .services import compute_baseline, simulate_price_change


def intro_page(request):
    screenshots = [
        {
            "title": "仪表盘总览",
            "caption": "集中展示商品数量、销售记录、累计销售额与利润趋势。",
            "image": "images/intro/dashboard.png",
        },
        {
            "title": "商品管理",
            "caption": "维护商品成本、售价、品类和价格敏感系数。",
            "image": "images/intro/products.png",
        },
        {
            "title": "策略模拟",
            "caption": "输入调价比例，预测销量变化与利润结果。",
            "image": "images/intro/simulate.png",
        },
        {
            "title": "数据分析",
            "caption": "按销售数据和模拟结果辅助定价决策。",
            "image": "images/intro/analysis.png",
        },
    ]

    features = [
        "商品、销售、模拟、分析一体化管理",
        "基于历史销售数据进行调价影响预测",
        "以图表方式呈现收益、利润与趋势变化",
    ]

    return render(
        request,
        "intro.html",
        {
            "screenshots": screenshots,
            "features": features,
            "system_name": "动态价格策略模拟与分析系统",
        },
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    next_url = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "注册成功")
            return redirect(next_url or "dashboard")
        messages.error(request, "注册失败，请检查输入")
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form, "next": next_url})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    next_url = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "登录成功")
            return redirect(next_url or "dashboard")
        messages.error(request, "用户名或密码错误")
    else:
        form = LoginForm(request)

    return render(request, "login.html", {"form": form, "next": next_url})


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    products = Product.objects.filter(created_by=request.user)
    sales = SalesRecord.objects.filter(product__created_by=request.user)[:8]
    simulations = SimulationResult.objects.filter(created_by=request.user)[:6]

    total_products = products.count()
    total_sales_rows = SalesRecord.objects.filter(product__created_by=request.user).count()

    revenue = 0.0
    profit = 0.0
    for r in SalesRecord.objects.filter(product__created_by=request.user):
        revenue += float(r.price) * int(r.quantity)
        profit += (float(r.price) - float(r.product.cost)) * int(r.quantity)

    chart_days = []
    chart_revenue = []
    chart_profit = []
    daily = {}
    for r in SalesRecord.objects.filter(product__created_by=request.user):
        k = str(r.sale_date)
        daily.setdefault(k, {"revenue": 0.0, "profit": 0.0})
        daily[k]["revenue"] += float(r.price) * int(r.quantity)
        daily[k]["profit"] += (float(r.price) - float(r.product.cost)) * int(r.quantity)

    for k in sorted(daily.keys())[-14:]:
        chart_days.append(k)
        chart_revenue.append(round(daily[k]["revenue"], 2))
        chart_profit.append(round(daily[k]["profit"], 2))

    context = {
        "products": products[:6],
        "sales": sales,
        "simulations": simulations,
        "kpis": {
            "total_products": total_products,
            "total_sales_rows": total_sales_rows,
            "revenue": round(revenue, 2),
            "profit": round(profit, 2),
        },
        "chart": {
            "days": chart_days,
            "revenue": chart_revenue,
            "profit": chart_profit,
        },
    }
    return render(request, "index.html", context)


@login_required
def product_list(request):
    products = Product.objects.filter(created_by=request.user).order_by("-updated_at")
    return render(request, "product_list.html", {"products": products})


@login_required
@require_http_methods(["GET", "POST"])
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            messages.success(request, "商品已添加")
            return redirect("product_list")
    else:
        form = ProductForm()

    return render(request, "product_form.html", {"form": form, "mode": "create"})


@login_required
@require_http_methods(["GET", "POST"])
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, created_by=request.user)

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "商品已更新")
            return redirect("product_list")
    else:
        form = ProductForm(instance=product)

    return render(request, "product_form.html", {"form": form, "mode": "edit"})


@login_required
@require_http_methods(["GET", "POST"])
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, created_by=request.user)

    if request.method == "POST":
        product.delete()
        messages.success(request, "商品已删除")
        return redirect("product_list")

    return render(request, "confirm_delete.html", {"object": product, "type": "商品"})


@login_required
def sales_list(request):
    records = SalesRecord.objects.filter(product__created_by=request.user)
    return render(request, "sales_list.html", {"records": records})


@login_required
@require_http_methods(["GET", "POST"])
def sales_create(request):
    if request.method == "POST":
        form = SalesRecordForm(request.POST)
        form.fields["product"].queryset = Product.objects.filter(created_by=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.product.created_by != request.user:
                messages.error(request, "无权限")
                return redirect("sales_list")
            obj.save()
            messages.success(request, "销售记录已添加")
            return redirect("sales_list")
    else:
        form = SalesRecordForm()
        form.fields["product"].queryset = Product.objects.filter(created_by=request.user)

    return render(request, "sales_form.html", {"form": form, "mode": "create"})


@login_required
@require_http_methods(["GET", "POST"])
def sales_edit(request, pk):
    record = get_object_or_404(SalesRecord, pk=pk, product__created_by=request.user)

    if request.method == "POST":
        form = SalesRecordForm(request.POST, instance=record)
        form.fields["product"].queryset = Product.objects.filter(created_by=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.product.created_by != request.user:
                messages.error(request, "无权限")
                return redirect("sales_list")
            obj.save()
            messages.success(request, "销售记录已更新")
            return redirect("sales_list")
    else:
        form = SalesRecordForm(instance=record)
        form.fields["product"].queryset = Product.objects.filter(created_by=request.user)

    return render(request, "sales_form.html", {"form": form, "mode": "edit"})


@login_required
@require_http_methods(["GET", "POST"])
def sales_delete(request, pk):
    record = get_object_or_404(SalesRecord, pk=pk, product__created_by=request.user)

    if request.method == "POST":
        record.delete()
        messages.success(request, "销售记录已删除")
        return redirect("sales_list")

    return render(request, "confirm_delete.html", {"object": record, "type": "销售记录"})


@login_required
@require_http_methods(["GET", "POST"])
def simulate(request):
    if request.method == "POST":
        form = SimulationForm(request.POST, user=request.user)
        if form.is_valid():
            product = form.cleaned_data["product"]
            price_change_rate = form.cleaned_data["price_change_rate"]

            base_sales, _ = compute_baseline(product)
            if base_sales == 0:
                messages.warning(request, "当前商品暂无销售记录，预测结果可能偏差较大")
            metrics = simulate_price_change(
                product=product, price_change_rate=price_change_rate, base_sales=base_sales
            )

            strategy = (
                f"调整 {round(metrics.price_change_rate * 100, 2)}% (敏感系数 {product.price_sensitivity})"
            )

            result = SimulationResult.objects.create(
                product=product,
                strategy=strategy,
                base_price=float(product.price),
                new_price=float(metrics.new_price),
                price_change_rate=float(metrics.price_change_rate),
                base_sales=int(metrics.base_sales),
                predicted_sales=int(metrics.predicted_sales),
                base_profit=float(metrics.base_profit),
                predicted_profit=float(metrics.predicted_profit),
                created_by=request.user,
            )

            messages.success(request, "模拟完成")
            return redirect("simulation_detail", pk=result.pk)
    else:
        form = SimulationForm(user=request.user)

    last_results = SimulationResult.objects.filter(created_by=request.user)[:8]

    return render(request, "simulation.html", {"form": form, "last_results": last_results})


@login_required
def simulation_detail(request, pk):
    result = get_object_or_404(SimulationResult, pk=pk, created_by=request.user)

    context = {
        "result": result,
        "price_change_percent": round(result.price_change_rate * 100, 2),
        "chart": {
            "labels": ["基准", "策略后"],
            "sales": [result.base_sales, result.predicted_sales],
            "profit": [round(result.base_profit, 2), round(result.predicted_profit, 2)],
            "price": [round(result.base_price, 2), round(result.new_price, 2)],
        },
    }
    return render(request, "result.html", context)


@login_required
def analysis_dashboard(request):
    form = AnalysisFilterForm(request.GET or None, user=request.user)
    records = (
        SalesRecord.objects.filter(product__created_by=request.user)
        .select_related("product")
        .order_by("sale_date", "id")
    )

    selected_product = None
    start_date = None
    end_date = None

    if form.is_valid():
        selected_product = form.cleaned_data.get("product")
        start_date = form.cleaned_data.get("start_date")
        end_date = form.cleaned_data.get("end_date")

        if selected_product:
            records = records.filter(product=selected_product)
        if start_date:
            records = records.filter(sale_date__gte=start_date)
        if end_date:
            records = records.filter(sale_date__lte=end_date)

    records_list = list(records)

    daily = {}
    total_revenue = 0.0
    total_profit = 0.0
    total_qty = 0

    product_summary = {}

    for r in records_list:
        k = str(r.sale_date)
        if k not in daily:
            daily[k] = {"revenue": 0.0, "profit": 0.0, "qty": 0}
        revenue = float(r.price) * int(r.quantity)
        profit = (float(r.price) - float(r.product.cost)) * int(r.quantity)

        daily[k]["revenue"] += revenue
        daily[k]["profit"] += profit
        daily[k]["qty"] += int(r.quantity)

        total_revenue += revenue
        total_profit += profit
        total_qty += int(r.quantity)

        pid = r.product_id
        if pid not in product_summary:
            product_summary[pid] = {
                "name": r.product.name,
                "revenue": 0.0,
                "profit": 0.0,
                "qty": 0,
            }
        product_summary[pid]["revenue"] += revenue
        product_summary[pid]["profit"] += profit
        product_summary[pid]["qty"] += int(r.quantity)

    days = []
    price_avg = []
    qty_list = []
    profit_list = []

    for k in sorted(daily.keys()):
        days.append(k)
        qty = daily[k]["qty"]
        avg_price = daily[k]["revenue"] / qty if qty else 0.0
        price_avg.append(round(avg_price, 2))
        qty_list.append(int(qty))
        profit_list.append(round(daily[k]["profit"], 2))

    avg_price_total = total_revenue / total_qty if total_qty else 0.0

    top_products = sorted(
        product_summary.values(), key=lambda x: x["profit"], reverse=True
    )[:5]

    context = {
        "form": form,
        "selected_product": selected_product,
        "kpis": {
            "revenue": round(total_revenue, 2),
            "profit": round(total_profit, 2),
            "quantity": total_qty,
            "avg_price": round(avg_price_total, 2),
        },
        "chart": {
            "days": days,
            "price_avg": price_avg,
            "quantity": qty_list,
            "profit": profit_list,
        },
        "top_products": top_products,
        "has_data": bool(records_list),
    }
    return render(request, "analysis.html", context)


# ============= 用户中心 =============


@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request):
    """当前登录用户查看与修改自己的资料。"""
    user = request.user

    if request.method == "POST":
        action = request.POST.get("action", "profile")
        profile_form = ProfileForm(instance=user)
        password_form = ProfilePasswordForm(user=user)

        if action == "password":
            password_form = ProfilePasswordForm(request.POST, user=user)
            if password_form.is_valid():
                if password_form.cleaned_data.get("change_password"):
                    user.set_password(password_form.cleaned_data["new_password1"])
                    user.save(update_fields=["password"])
                    update_session_auth_hash(request, user)
                    messages.success(request, "密码已更新")
                else:
                    messages.info(request, "未填写密码字段，已忽略")
                return redirect("profile")
        else:
            profile_form = ProfileForm(request.POST, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "资料已更新")
                return redirect("profile")
    else:
        profile_form = ProfileForm(instance=user)
        password_form = ProfilePasswordForm(user=user)

    context = {
        "profile_form": profile_form,
        "password_form": password_form,
        "target_user": user,
    }
    return render(request, "profile.html", context)


def _superuser_required(view_func):
    """仅超级管理员可访问。"""
    return user_passes_test(lambda u: u.is_authenticated and u.is_superuser)(view_func)


def _staff_required(view_func):
    """超级管理员或管理员（is_staff）可访问。"""
    return user_passes_test(
        lambda u: u.is_authenticated and (u.is_staff or u.is_superuser)
    )(view_func)


@login_required
@_staff_required
def user_list(request):
    users = User.objects.all().order_by("-is_superuser", "-is_staff", "username")
    return render(request, "user_list.html", {"users": users})


@login_required
@_staff_required
@require_http_methods(["GET", "POST"])
def user_edit(request, pk):
    target = get_object_or_404(User, pk=pk)
    editing_self = request.user.pk == target.pk

    # 管理员（非超管）越级拦截：不能编辑超级管理员（编辑自己除外）
    if (
        not request.user.is_superuser
        and target.is_superuser
        and not editing_self
    ):
        messages.error(request, "你没有权限修改超级管理员账号")
        return redirect("user_list")

    if request.method == "POST":
        action = request.POST.get("action", "profile")
        user_form = AdminUserForm(
            instance=target, current_user=request.user, target_user=target
        )
        password_form = AdminPasswordResetForm(target_user=target)

        if action == "password":
            # 管理员不能为超级管理员重置密码（再次防御）
            if not request.user.is_superuser and target.is_superuser and not editing_self:
                messages.error(request, "你没有权限重置超级管理员的密码")
                return redirect("user_list")
            password_form = AdminPasswordResetForm(request.POST, target_user=target)
            if password_form.is_valid():
                if password_form.cleaned_data.get("change_password"):
                    target.set_password(password_form.cleaned_data["new_password1"])
                    target.save(update_fields=["password"])
                    if editing_self:
                        update_session_auth_hash(request, target)
                    messages.success(request, f"已为用户 {target.username} 重置密码")
                else:
                    messages.info(request, "未填写新密码，已忽略")
                return redirect("user_edit", pk=target.pk)
        else:
            user_form = AdminUserForm(
                request.POST,
                instance=target,
                current_user=request.user,
                target_user=target,
            )
            if user_form.is_valid():
                user_form.save()
                messages.success(request, f"用户 {target.username} 资料已更新")
                return redirect("user_edit", pk=target.pk)
    else:
        user_form = AdminUserForm(
            instance=target, current_user=request.user, target_user=target
        )
        password_form = AdminPasswordResetForm(target_user=target)

    context = {
        "user_form": user_form,
        "password_form": password_form,
        "target_user": target,
        "editing_self": editing_self,
        "can_edit_superuser_field": request.user.is_superuser,
    }
    return render(request, "user_form.html", context)
